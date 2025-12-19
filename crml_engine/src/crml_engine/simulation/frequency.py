"""
Frequency generation logic for CRML simulation.
"""
import numpy as np
from typing import Optional, Dict, List, Any
from .utils import parse_numberish_value

class FrequencyEngine:
    """Handles generating the number of loss events per simulation run."""

    @staticmethod
    def _apply_rate_multiplier(
        total_lambda: float,
        *,
        rate_multiplier: Optional[object],
        n_runs: int,
    ) -> object:
        if rate_multiplier is None:
            return total_lambda

        rm = rate_multiplier
        if isinstance(rm, (int, float, np.floating)):
            return float(total_lambda) * float(rm)

        rm_arr = np.asarray(rm, dtype=np.float64)
        if rm_arr.shape != (n_runs,):
            raise ValueError("rate_multiplier must be a scalar or shape (n_runs,)")
        return float(total_lambda) * rm_arr

    @staticmethod
    def _generate_poisson(
        *,
        params: Any,
        n_runs: int,
        cardinality: int,
        uniforms: Optional[np.ndarray],
        rate_multiplier: Optional[object],
        rng: np.random.Generator,
    ) -> np.ndarray:
        lambda_val = float(params.lambda_) if params and getattr(params, "lambda_", None) is not None else 0.0
        if lambda_val <= 0:
            return np.zeros(n_runs, dtype=int)

        total_lambda: float = lambda_val * int(cardinality)
        total_lambda = FrequencyEngine._apply_rate_multiplier(
            total_lambda,
            rate_multiplier=rate_multiplier,
            n_runs=n_runs,
        )

        if uniforms is not None:
            from scipy.stats import poisson

            return poisson.ppf(uniforms, total_lambda).astype(int)

        return rng.poisson(total_lambda, n_runs)

    @staticmethod
    def _generate_gamma(
        *,
        params: Any,
        n_runs: int,
        cardinality: int,
        uniforms: Optional[np.ndarray],
        rng: np.random.Generator,
    ) -> np.ndarray:
        shape_val = float(params.shape) if params and getattr(params, "shape", None) is not None else 0.0
        scale_val = float(params.scale) if params and getattr(params, "scale", None) is not None else 0.0

        if shape_val <= 0 or scale_val <= 0:
            return np.zeros(n_runs, dtype=int)

        if uniforms is not None:
            from scipy.stats import gamma

            rates = gamma.ppf(uniforms, a=shape_val, scale=scale_val)
        else:
            rates = rng.gamma(shape_val, scale_val, n_runs)

        return np.maximum(0, np.round(rates * int(cardinality))).astype(int)

    @staticmethod
    def _generate_hierarchical_gamma_poisson(
        *,
        params: Any,
        n_runs: int,
        cardinality: int,
        uniforms: Optional[np.ndarray],
        rng: np.random.Generator,
    ) -> np.ndarray:
        alpha_base = float(params.alpha_base) if params and getattr(params, "alpha_base", None) is not None else 1.5
        beta_base = float(params.beta_base) if params and getattr(params, "beta_base", None) is not None else 1.5

        shape_val = alpha_base
        scale_val = beta_base

        if shape_val <= 0 or scale_val <= 0:
            return np.zeros(n_runs, dtype=int)

        if uniforms is not None:
            from scipy.stats import gamma

            sampled_lambdas = gamma.ppf(uniforms, a=shape_val, scale=scale_val)
        else:
            sampled_lambdas = rng.gamma(shape_val, scale_val, n_runs)

        total_lambdas = sampled_lambdas * int(cardinality)
        # Poisson sampling supports array-valued lambda.
        return rng.poisson(total_lambdas)
    
    @staticmethod
    def generate_frequency(
        freq_model: str, 
        params: Any, 
        n_runs: int, 
        cardinality: int,
        seed: Optional[int] = None,
        uniforms: Optional[np.ndarray] = None,
        rate_multiplier: Optional[object] = None,
    ) -> np.ndarray:
        """Generate per-run event counts for the configured frequency model.

        Supported models:
            - "poisson": Poisson($\lambda$) with $\lambda$ scaled by `cardinality`.
            - "gamma": Gamma(shape, scale) sampled as a *rate-like* quantity,
              then scaled by `cardinality` and rounded.
            - "hierarchical_gamma_poisson": Gamma-Poisson compound process
              (negative-binomial equivalent).

        Args:
            freq_model: Model name.
            params: Parameters object (typically a Pydantic model) expected to
                provide attributes consistent with the chosen model.
            n_runs: Number of Monte Carlo iterations.
            cardinality: Exposure multiplier (e.g., number of assets).
            seed: Optional seed (currently the engine uses NumPy global RNG;
                this argument is reserved for future local RNG handling).
            uniforms: Optional uniform variates in (0, 1) used for inverse-CDF
                sampling in some branches to support copula correlation.
            rate_multiplier: Optional scalar or per-run multiplier applied to
                the computed rate in the poisson branch.

        Returns:
            Integer numpy array of shape (n_runs,) with event counts.

        Raises:
            ValueError: If `rate_multiplier` is an array with wrong shape.
        """
        # Note: seed is handled globally by numpy in the main engine, 
        # but passed here if we ever want local random states.

        rng = np.random.default_rng(seed)

        if freq_model == 'poisson':
            return FrequencyEngine._generate_poisson(
                params=params,
                n_runs=n_runs,
                cardinality=cardinality,
                uniforms=uniforms,
                rate_multiplier=rate_multiplier,
                rng=rng,
            )

        if freq_model == 'gamma':
            return FrequencyEngine._generate_gamma(
                params=params,
                n_runs=n_runs,
                cardinality=cardinality,
                uniforms=uniforms,
                rng=rng,
            )

        if freq_model == 'hierarchical_gamma_poisson':
            return FrequencyEngine._generate_hierarchical_gamma_poisson(
                params=params,
                n_runs=n_runs,
                cardinality=cardinality,
                uniforms=uniforms,
                rng=rng,
            )

        # Fallback or unknown model
        return np.zeros(n_runs, dtype=int)
