"""
Severity generation logic for CRML simulation.
"""
import numpy as np
import math
import logging
from typing import Optional, Dict, List, Any, Tuple
from ..models.fx_model import FXConfig, convert_currency

class SeverityEngine:
    """Handles generating loss amounts for each event."""

    @staticmethod
    def _resolve_currency(params: Any, *, base_currency: str) -> str:
        cur = params.currency if params and getattr(params, "currency", None) else base_currency
        return cur

    @staticmethod
    def _lognormal_mu_from_params(
        *,
        params: Any,
        sev_currency: str,
        base_currency: str,
        fx_config: FXConfig,
    ) -> float:
        has_median = params is not None and getattr(params, "median", None) is not None
        has_mu = params is not None and getattr(params, "mu", None) is not None

        if has_median and has_mu:
            raise ValueError("Cannot use both 'median' and 'mu'. Choose one (median is recommended).")

        if has_median:
            median_val = convert_currency(params.median, sev_currency, base_currency, fx_config)
            if median_val <= 0:
                raise ValueError(f"Median parameter must be positive. Got: {median_val}")
            return float(math.log(float(median_val)))

        if has_mu:
            mu_in = float(params.mu)
            if sev_currency != base_currency:
                rate = convert_currency(1.0, sev_currency, base_currency, fx_config)
                return float(mu_in + math.log(rate))
            return float(mu_in)

        raise ValueError(
            "Lognormal distribution requires either 'median' or 'mu' (or provide 'single_losses' for auto-calibration)"
        )

    @staticmethod
    def _lognormal_sigma_from_params(params: Any) -> float:
        sigma_raw = float(params.sigma) if params and getattr(params, "sigma", None) else 0.0
        if sigma_raw <= 0:
            raise ValueError("Sigma parameter must be positive")
        return float(sigma_raw)

    @staticmethod
    def _lognormal_params_from_explicit_params(
        *,
        params: Any,
        base_currency: str,
        fx_config: FXConfig,
    ) -> tuple[float, float]:
        sev_currency = SeverityEngine._resolve_currency(params, base_currency=base_currency)
        mu_val = SeverityEngine._lognormal_mu_from_params(
            params=params,
            sev_currency=sev_currency,
            base_currency=base_currency,
            fx_config=fx_config,
        )
        sigma_val = SeverityEngine._lognormal_sigma_from_params(params)
        return mu_val, sigma_val

    @classmethod
    def _generate_lognormal(
        cls,
        *,
        params: Any,
        total_events: int,
        base_currency: str,
        fx_config: FXConfig,
        rng: np.random.Generator,
    ) -> np.ndarray:
        # 1) Auto-calibration from empirical single-event losses.
        if params and hasattr(params, 'single_losses') and params.single_losses is not None:
            try:
                mu_val, sigma_val = cls.calibrate_lognormal_from_single_losses(
                    params.single_losses,
                    getattr(params, "currency", None),
                    base_currency,
                    fx_config,
                )
            except Exception as e:
                # Keep behavior: don't crash whole sim on bad config.
                logging.error(e)
                return np.zeros(total_events)
        else:
            mu_val, sigma_val = cls._lognormal_params_from_explicit_params(
                params=params,
                base_currency=base_currency,
                fx_config=fx_config,
            )

        return rng.lognormal(mu_val, sigma_val, total_events)

    @staticmethod
    def _generate_gamma(
        *,
        params: Any,
        total_events: int,
        base_currency: str,
        fx_config: FXConfig,
        rng: np.random.Generator,
    ) -> np.ndarray:
        shape = float(params.shape) if params and getattr(params, "shape", None) else 0.0
        scale = float(params.scale) if params and getattr(params, "scale", None) else 0.0

        if shape <= 0 or scale <= 0:
            return np.zeros(total_events)

        sev_currency = params.currency if params and getattr(params, "currency", None) else base_currency
        scale = convert_currency(scale, sev_currency, base_currency, fx_config)
        return rng.gamma(shape, scale, total_events)

    @classmethod
    def _generate_mixture_first_component(
        cls,
        *,
        components: Optional[List[Dict[str, Any]]],
        total_events: int,
        fx_config: FXConfig,
    ) -> np.ndarray:
        if not components:
            return np.zeros(total_events)

        # Reference engine limitation: only the first component is used.
        # (This matches historical behavior; mixture weights are not applied.)
        first = components[0]

        from .utils import parse_numberish_value

        def _safe_parse(v: Any):
            if v is None:
                return None
            return parse_numberish_value(v)

        if 'lognormal' in first:
            ln_data = first['lognormal']

            class MockParams:
                pass

            p = MockParams()
            p.single_losses = ln_data.get('single_losses')
            p.median = _safe_parse(ln_data.get('median'))
            p.mu = _safe_parse(ln_data.get('mu'))
            p.sigma = _safe_parse(ln_data.get('sigma'))
            p.currency = ln_data.get('currency')
            return cls.generate_severity('lognormal', p, None, total_events, fx_config)

        if 'gamma' in first:
            g_data = first['gamma']

            class MockParams:
                pass

            p = MockParams()
            p.shape = _safe_parse(g_data.get('shape'))
            p.scale = _safe_parse(g_data.get('scale'))
            p.currency = g_data.get('currency')
            return cls.generate_severity('gamma', p, None, total_events, fx_config)

        return np.zeros(total_events)

    @staticmethod
    def calibrate_lognormal_from_single_losses(
        single_losses: list,
        currency: Optional[str],
        base_currency: str,
        fx_config: FXConfig,
    ) -> Tuple[float, float]:
        """Calibrate lognormal parameters from empirical single-event losses.

        This helper interprets `single_losses` as realized *single-event*
        severities, converts them to `base_currency`, then estimates:

            - $\mu = \ln(\mathrm{median}(losses))$
            - $\sigma = \mathrm{std}(\ln(losses))$

        Args:
            single_losses: Sequence of single-event losses. Values may be
                numeric or string-like (e.g., "1 000", "2,500").
            currency: Currency code/symbol for `single_losses`. If None, uses
                `fx_config.base_currency`.
            base_currency: Currency code to calibrate into.
            fx_config: FX configuration for currency conversion.

        Returns:
            (mu, sigma) parameters for a lognormal distribution in log-space.

        Raises:
            ValueError: If there are fewer than 2 losses or any loss is <= 0.
        """
        if not single_losses or len(single_losses) < 2:
            raise ValueError("single_losses must be an array with at least 2 values")

        sev_currency = currency or fx_config.base_currency
        
        from .utils import parse_numberish_value
        # Convert all losses to base currency first
        # Use parse_numberish_value to ensure we handle strings like "1 000" correctly
        losses_base = [
            convert_currency(parse_numberish_value(v), sev_currency, base_currency, fx_config) 
            for v in single_losses
        ]

        if any(v <= 0 for v in losses_base):
            raise ValueError("single_losses values must be positive")

        median_val = float(np.median(losses_base))
        mu_val = math.log(median_val)
        
        log_losses = [math.log(v) for v in losses_base]
        sigma_val = float(np.std(log_losses))
        
        return mu_val, sigma_val

    @classmethod
    def generate_severity(
        cls,
        sev_model: str,
        params: Any,
        components: Optional[List[Dict[str, Any]]],
        total_events: int,
        fx_config: FXConfig,
        seed: Optional[int] = None,
    ) -> np.ndarray:
        """Generate per-event severity samples in the FX base currency.

        Supported models:
            - "lognormal": parameterized by (median or mu) and sigma, or by
              empirical calibration via `single_losses`.
            - "gamma": parameterized by (shape, scale).
            - "mixture": reference implementation with limited handling.

        Currency handling:
            Severity parameters may specify a currency; values are converted to
            `fx_config.base_currency` before sampling.

        Args:
            sev_model: Model name.
            params: Parameter object (typically a Pydantic model) expected to
                provide attributes consistent with the chosen model.
            components: Mixture components for the "mixture" model.
            total_events: Number of per-event samples to generate.
            fx_config: FX configuration used to normalize values.

        Returns:
            Float numpy array of shape (total_events,) representing per-event
            severities.

        Raises:
            ValueError: For invalid parameter combinations (e.g. both median
                and mu for lognormal) or invalid values (e.g. non-positive
                sigma).
        """
        if total_events <= 0:
            return np.array([])
            
        base_currency = fx_config.base_currency
        rng = np.random.default_rng(seed)

        if sev_model == 'lognormal':
            return cls._generate_lognormal(
                params=params,
                total_events=total_events,
                base_currency=base_currency,
                fx_config=fx_config,
                rng=rng,
            )

        if sev_model == 'gamma':
            return cls._generate_gamma(
                params=params,
                total_events=total_events,
                base_currency=base_currency,
                fx_config=fx_config,
                rng=rng,
            )

        if sev_model == 'mixture':
            return cls._generate_mixture_first_component(
                components=components,
                total_events=total_events,
                fx_config=fx_config,
            )

        return np.zeros(total_events)
