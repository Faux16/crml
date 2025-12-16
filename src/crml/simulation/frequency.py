"""
Frequency generation logic for CRML simulation.
"""
import numpy as np
from typing import Optional, Dict, List, Any
from .utils import parse_numberish_value

class FrequencyEngine:
    """Handles generating the number of loss events per simulation run."""
    
    @staticmethod
    def generate_frequency(
        freq_model: str, 
        params: Any, 
        n_runs: int, 
        cardinality: int,
        seed: Optional[int] = None,
        uniforms: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Generate an array of shape (n_runs,) containing event counts.
        
        Args:
            freq_model: 'poisson', 'gamma', or 'hierarchical_gamma_poisson'
            params: Pydantic model or dict containing parameters
            n_runs: Number of simulation iterations
            cardinality: Total number of assets (multiplier for lambda)
            seed: Random seed (optional, but usually set at engine level)
            uniforms: Optional correlated uniform random numbers (0, 1) to use for sampling (Copula method)
            
        Returns:
            np.ndarray of integers (event counts per run)
        """
        # Note: seed is handled globally by numpy in the main engine, 
        # but passed here if we ever want local random states.
        
        if freq_model == 'poisson':
            lambda_val = float(params.lambda_) if params and params.lambda_ is not None else 0.0
            if lambda_val <= 0:
                return np.zeros(n_runs, dtype=int)
                
            # Scale lambda by asset count
            total_lambda = lambda_val * cardinality
            
            if uniforms is not None:
                # Use Copula method (Inverse CDF)
                from scipy.stats import poisson
                # PPF returns k such that P(X<=k) >= u
                # inputs: (q, mu) where q is probability
                return poisson.ppf(uniforms, total_lambda).astype(int)
            else:
                return np.random.poisson(total_lambda, n_runs)
            
        elif freq_model == 'gamma':
            # Direct Gamma sampling for frequency (often used as a proxy for uncertainty)
            shape_val = float(params.shape) if params and params.shape is not None else 0.0
            scale_val = float(params.scale) if params and params.scale is not None else 0.0
            
            if shape_val <= 0 or scale_val <= 0:
                return np.zeros(n_runs, dtype=int)
            
            if uniforms is not None:
                from scipy.stats import gamma
                # Gamma args: a (shape), scale=scale
                rates = gamma.ppf(uniforms, a=shape_val, scale=scale_val)
            else:
                # Sample continuous rates
                rates = np.random.gamma(shape_val, scale_val, n_runs)
                
            # Scale by cardinality and round to nearest integer
            return np.maximum(0, np.round(rates * cardinality)).astype(int)
            
        elif freq_model == 'hierarchical_gamma_poisson':
            # True Compound Process (Negative Binomial equivalent) implementation
            # 1. Sample Lambda for each run from Gamma(alpha, beta)
            # 2. Sample N for each run from Poisson(Lambda)
            
            alpha_base = float(params.alpha_base) if params and params.alpha_base is not None else 1.5
            beta_base = float(params.beta_base) if params and params.beta_base is not None else 1.5
            
            # Gamma parameters: shape=alpha, scale=beta (or 1/beta depending on convention)
            # In CRML, we assume scale parameter convention for consistency with 'gamma' model above
            # If using rate parameter (beta), scale = 1/beta
            
            shape_val = alpha_base
            scale_val = beta_base
            
            if shape_val <= 0 or scale_val <= 0:
                return np.zeros(n_runs, dtype=int)
            
            # Step 1: Sample 'true' lambda for this scenario/year from Gamma
            if uniforms is not None:
                from scipy.stats import gamma, poisson
                # We reuse the same uniforms for the Gamma step to induce correlation in the underlying rate.
                # Ideally, we might want *two* correlated uniforms per run for full NORTA, 
                # but correlating the rate parameter is the primary driver of correlation here.
                sampled_lambdas = gamma.ppf(uniforms, a=shape_val, scale=scale_val)
                total_lambdas = sampled_lambdas * cardinality
                # Step 2: Poisson realization (uncorrelated step given lambda, or re-use u?)
                # If we reuse U, we get perfect correlation given lambda.
                # Standard practice: Sample Poisson given Lambda.
                return np.random.poisson(total_lambdas)
            else:
                # Step 1: Sample 'true' lambda for this scenario/year from Gamma
                # This represents parameter uncertainty about the frequency
                sampled_lambdas = np.random.gamma(shape_val, scale_val, n_runs)
                
                # Step 2: Scale by cardinality
                total_lambdas = sampled_lambdas * cardinality
                
                # Step 3: Sample realization from Poisson
                return np.random.poisson(total_lambdas)
            
        else:
            # Fallback or unknown model
            return np.zeros(n_runs, dtype=int)
