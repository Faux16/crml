"""
Severity generation logic for CRML simulation.
"""
import numpy as np
import math
from typing import Optional, Dict, List, Any, Tuple
from ..models.fx_model import FXConfig, convert_currency

class SeverityEngine:
    """Handles generating loss amounts for each event."""

    @staticmethod
    def calibrate_lognormal_from_single_losses(
        single_losses: list,
        currency: Optional[str],
        base_currency: str,
        fx_config: FXConfig,
    ) -> Tuple[float, float]:
        """
        Calibrate lognormal mu/sigma from a list of single-event loss amounts.
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
        fx_config: FXConfig
    ) -> np.ndarray:
        """
        Generate an array of loss amounts for specified number of events.
        
        Args:
            sev_model: 'lognormal', 'gamma', or 'mixture'
            params: Parameters object (Pydantic)
            components: List of components for mixture models
            total_events: Total number of losses to generate
            fx_config: Currency configuration
            
        Returns:
            np.ndarray of floats (loss amounts)
        """
        if total_events <= 0:
            return np.array([])
            
        base_currency = fx_config.base_currency

        if sev_model == 'lognormal':
            mu_val, sigma_val = 0.0, 0.0
            
            # 1. Check for single_losses auto-calibration
            if params and hasattr(params, 'single_losses') and params.single_losses is not None:
                try:
                    mu_val, sigma_val = cls.calibrate_lognormal_from_single_losses(
                        params.single_losses,
                        params.currency,
                        base_currency,
                        fx_config
                    )
                except Exception as e:
                    # In a real engine we might raise or log, 
                    # but here we return zeros to avoid crashing the whole sim if config is bad
                    # The validator should catch this earlier.
                    return np.zeros(total_events)
            else:
                # 2. Standard parameters
                sev_currency = params.currency if params and params.currency else base_currency
                
                # Validation: Cannot have both median and mu
                if params and params.median is not None and params.mu is not None:
                     raise ValueError("Cannot use both 'median' and 'mu'. Choose one (median is recommended).")

                # Median or Mu
                if params and params.median is not None:
                    # Parse median
                    median_val = params.median
                    # Convert to base currency
                    median_val = convert_currency(median_val, sev_currency, base_currency, fx_config)
                    if median_val <= 0: 
                        raise ValueError(f"Median parameter must be positive. Got: {median_val}")
                    mu_val = math.log(median_val)
                elif params and params.mu is not None:
                    mu_in = float(params.mu)
                    # Adjust mu for currency: new_mu = old_mu + ln(rate)
                    if sev_currency != base_currency:
                        rate = convert_currency(1.0, sev_currency, base_currency, fx_config)
                        mu_val = mu_in + math.log(rate)
                    else:
                        mu_val = mu_in
                else:
                     raise ValueError("Lognormal distribution requires either 'median' or 'mu' (or provide 'single_losses' for auto-calibration)")

                if not params or not params.sigma:
                     raise ValueError("Lognormal distribution requires 'sigma'")

                sigma_val = float(params.sigma) if params and params.sigma else 0.0
                if sigma_val <= 0: 
                     raise ValueError("Sigma parameter must be positive")

            return np.random.lognormal(mu_val, sigma_val, total_events)

        elif sev_model == 'gamma':
            shape = float(params.shape) if params and params.shape else 0.0
            scale = float(params.scale) if params and params.scale else 0.0
            
            if shape <= 0 or scale <= 0: return np.zeros(total_events)
            
            sev_currency = params.currency if params and params.currency else base_currency
            # Scale parameter scales linearly with currency
            scale = convert_currency(scale, sev_currency, base_currency, fx_config)
            
            return np.random.gamma(shape, scale, total_events)

        elif sev_model == 'mixture':
            if not components:
                return np.zeros(total_events)
            
            # Simplified mixture handling: For now, just pick the first component 
            # (as was done in the original runtime.py). 
            # TODO: Implement proper weighted mixture sampling
            
            first = components[0]
            
            # Helper to parse potential string numbers
            from .utils import parse_numberish_value
            def _safe_parse(v):
                if v is None: return None
                return parse_numberish_value(v)

            if 'lognormal' in first:
                ln_data = first['lognormal']
                class MockParams:
                    pass
                p = MockParams()
                p.single_losses = ln_data.get('single_losses') # handled by calibrate if present
                p.median = _safe_parse(ln_data.get('median'))
                p.mu = _safe_parse(ln_data.get('mu'))
                p.sigma = _safe_parse(ln_data.get('sigma'))
                p.currency = ln_data.get('currency')
                
                return cls.generate_severity('lognormal', p, None, total_events, fx_config)
                
            elif 'gamma' in first:
                g_data = first['gamma']
                class MockParams:
                    pass
                p = MockParams()
                p.shape = _safe_parse(g_data.get('shape'))
                p.scale = _safe_parse(g_data.get('scale'))
                p.currency = g_data.get('currency')
                
                return cls.generate_severity('gamma', p, None, total_events, fx_config)
            
            return np.zeros(total_events)

        return np.zeros(total_events)
