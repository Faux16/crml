import pytest
import numpy as np
from crml.simulation.engine import run_monte_carlo

# Synthetic YAML for a multi-scenario model
MULTI_SCENARIO_YAML = """
crml: "1.1"
meta:
  name: "Multi-Scenario Test"
model:
  assets:
    - name: "Database"
      cardinality: 1
    - name: "Laptop"
      cardinality: 1

  frequency:
    models:
      - asset: "Database"
        model: "poisson"
        parameters:
          lambda: 2.0  # ~2 events/year
      - asset: "Laptop"
        model: "poisson"
        parameters:
          lambda: 5.0  # ~5 events/year

  severity:
    models:
      - asset: "Database"
        model: "lognormal"
        parameters:
          median: 1000
          sigma: 0.5
      - asset: "Laptop"
        model: "lognormal"
        parameters:
          median: 100
          sigma: 0.1
"""

def test_multi_scenario_eal_aggregation():
    """
    Test that the engine correctly aggregates losses from multiple scenarios.
    
    Scenario 1 (Database):
      Frequency: Poisson(2.0)
      Severity: Lognormal(median=1000, sigma=0.5)
      Mean Severity ~= exp(ln(1000) + 0.5^2/2) = 1000 * exp(0.125) ~= 1133
      Expected Annual Loss ~= 2.0 * 1133 = 2266
      
    Scenario 2 (Laptop):
      Frequency: Poisson(5.0)
      Severity: Lognormal(median=100, sigma=0.1)
      Mean Severity ~= exp(ln(100) + 0.1^2/2) = 100 * exp(0.005) ~= 100.5
      Expected Annual Loss ~= 5.0 * 100.5 = 502.5
      
    Total Expected EAL ~= 2266 + 502.5 = 2768.5
    """
    result = run_monte_carlo(MULTI_SCENARIO_YAML, n_runs=10000, seed=42)
    
    assert result.success, f"Simulation failed: {result.errors}"
    
    eal = result.metrics.eal
    print(f"Calculated EAL: {eal}")
    
    # Allow 5% margin of error for MC variability
    expected_eal = 2768.5
    margin = expected_eal * 0.05
    
    assert expected_eal - margin <= eal <= expected_eal + margin, \
        f"EAL {eal} not within 5% of expected {expected_eal}"

def test_fallback_to_global_severity():
    """
    Test that if a severity model is missing for an asset, it falls back to the global model.
    """
    YAML_FALLBACK = """
    crml: "1.1"
    meta: {name: "Fallback Test"}
    model:
      assets: [{name: "A", cardinality: 1}]
      frequency:
        models:
          - asset: "A"
            model: "poisson"
            parameters: {lambda: 10}
      severity:
        model: "lognormal"
        parameters: {median: 50, sigma: 0.1}
    """
    result = run_monte_carlo(YAML_FALLBACK, n_runs=1000, seed=42)
    assert result.success
    # Should run with global severity
    assert result.metrics.eal > 0
