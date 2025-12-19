import pytest
import numpy as np
from crml_engine.simulation.engine import run_monte_carlo

def test_high_correlation_poisson():
    """
    Test that high correlation (0.99) results in highly correlated event counts.
    """
    # Note: under the strict scenario-only schema, correlation is a portfolio concern.
    # This test validates correlation behavior directly using the copula method.
    # Need to access internal frequency counts, but run_monte_carlo returns aggregated result.
    # However, we can use the engine internals or check variance of sum?
    # Var(A+B) = Var(A) + Var(B) + 2*Cov(A,B)
    # If Corr=1, Cov is high, Var(Sum) is max.
    # If Corr=0, Var(Sum) is lower.
    
    # Let's run simulation via engine and capture metrics if possible, 
    # OR simpler: check that EAL is consistent, but to check correlation strictly we need the raw counts.
    
    # Since run_monte_carlo doesn't expose raw counts, let's use the internal logic directly 
    # by importing FrequencyEngine and doing what the engine does.
    
    from crml_engine.simulation.frequency import FrequencyEngine
    from scipy.stats import norm
    
    n_runs = 10000
    # Manual Copula Generation
    cov = np.array([[1.0, 0.99], [0.99, 1.0]])
    L = np.linalg.cholesky(cov)
    Z = np.random.standard_normal((n_runs, 2)) @ L.T
    U = norm.cdf(Z)
    
    # Generate counts
    counts_A = FrequencyEngine.generate_frequency('poisson', type('Params', (), {'lambda_': 5})(), n_runs, 1, uniforms=U[:,0])
    counts_B = FrequencyEngine.generate_frequency('poisson', type('Params', (), {'lambda_': 5})(), n_runs, 1, uniforms=U[:,1])
    
    # Check correlation
    corr = np.corrcoef(counts_A, counts_B)[0,1]
    print(f"Measured Correlation: {corr}")
    assert corr > 0.9, f"Expected correlation > 0.9, got {corr}"

def test_zero_correlation_poisson():
    """
    Test that zero correlation results in uncorrelated event counts.
    """
    from crml_engine.simulation.frequency import FrequencyEngine
    from scipy.stats import norm
    
    n_runs = 10000
    # Manual Copula Generation
    cov = np.array([[1.0, 0.0], [0.0, 1.0]])
    L = np.linalg.cholesky(cov)
    Z = np.random.standard_normal((n_runs, 2)) @ L.T
    U = norm.cdf(Z)
    
    counts_A = FrequencyEngine.generate_frequency('poisson', type('Params', (), {'lambda_': 5})(), n_runs, 1, uniforms=U[:,0])
    counts_B = FrequencyEngine.generate_frequency('poisson', type('Params', (), {'lambda_': 5})(), n_runs, 1, uniforms=U[:,1])
    
    corr = np.corrcoef(counts_A, counts_B)[0,1]
    print(f"Measured Correlation: {corr}")
    assert abs(corr) < 0.05, f"Expected correlation near 0, got {corr}"
