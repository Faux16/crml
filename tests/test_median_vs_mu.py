import pytest
import numpy as np
from crml.runtime import run_simulation


def test_median_equivalent_to_mu():
    """Verify that median=X produces same results as mu=ln(X)."""
    
    median_value = 100000
    mu_value = np.log(median_value)  # ln(100000) ≈ 11.513
    
    median_model = f"""
crml: "1.1"
meta:
  name: "median-test"
model:
  frequency:
    model: poisson
    parameters:
      lambda: 1.0
  severity:
    model: lognormal
    parameters:
      median: {median_value}
      currency: USD
      sigma: 1.2
"""
    
    mu_model = f"""
crml: "1.1"
meta:
  name: "mu-test"
model:
  frequency:
    model: poisson
    parameters:
      lambda: 1.0
  severity:
    model: lognormal
    parameters:
      mu: {mu_value}
      currency: USD
      sigma: 1.2
"""
    
    n_runs = 50000
    seed = 42
    
    res_median = run_simulation(median_model, n_runs=n_runs, seed=seed)
    res_mu = run_simulation(mu_model, n_runs=n_runs, seed=seed)
    
    assert res_median["success"] is True
    assert res_mu["success"] is True
    
    # With same seed and large sample, EALs should be very close
    eal_median = res_median["metrics"]["eal"]
    eal_mu = res_mu["metrics"]["eal"]
    
    # Allow 2% tolerance for Monte Carlo noise
    relative_diff = abs(eal_median - eal_mu) / max(1.0, eal_median)
    assert relative_diff < 0.02, f"EAL difference too large: {eal_median} vs {eal_mu}"
    
    # Check VaR metrics also match
    var95_median = res_median["metrics"]["var_95"]
    var95_mu = res_mu["metrics"]["var_95"]
    var95_diff = abs(var95_median - var95_mu) / max(1.0, var95_median)
    assert var95_diff < 0.03, f"VaR95 difference too large: {var95_median} vs {var95_mu}"


def test_median_mu_conflict_rejected():
    """Verify that providing both median and mu is rejected."""
    
    conflicting_model = """
crml: "1.1"
meta:
  name: "conflict-test"
model:
  frequency:
    model: poisson
    parameters:
      lambda: 1.0
  severity:
    model: lognormal
    parameters:
      median: 100000
      mu: 11.513
      sigma: 1.2
"""
    
    result = run_simulation(conflicting_model, n_runs=100)
    assert result["success"] is False
    assert len(result["errors"]) > 0


def test_median_with_space_separator():
    """Verify that median accepts space-separated numbers for readability."""
    
    model = """
crml: "1.1"
meta:
  name: "space-test"
model:
  frequency:
    model: poisson
    parameters:
      lambda: 1.0
  severity:
    model: lognormal
    parameters:
      median: "100 000"  # 100,000 with space separator
      currency: USD
      sigma: 1.2
"""
    
    result = run_simulation(model, n_runs=1000, seed=42)
    assert result["success"] is True
    # Median should be parsed as 100000
    assert result["metrics"]["eal"] > 0


def test_missing_median_and_mu_rejected():
    """Verify that lognormal requires either median or mu."""
    
    missing_model = """
crml: "1.1"
meta:
  name: "missing-test"
model:
  frequency:
    model: poisson
    parameters:
      lambda: 1.0
  severity:
    model: lognormal
    parameters:
      sigma: 1.2
"""
    
    result = run_simulation(missing_model, n_runs=100)
    assert result["success"] is False
    assert any("median" in str(err).lower() or "mu" in str(err).lower() 
               for err in result["errors"])
