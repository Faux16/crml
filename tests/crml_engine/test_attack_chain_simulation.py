import pytest
import numpy as np

from crml_engine.simulation.engine import run_monte_carlo
from crml_lang.models.scenario_model import load_crml_from_yaml_str

def test_attack_chain_frequency_reduction():
    """Test that attack chain probabilities reduce the effective frequency."""
    
    # Base scenario with high lambda (100) to get reliable counts
    base_yaml = """
    crml_scenario: "1.0"
    meta:
      name: "Test Chain"
    scenario:
      frequency:
        model: "poisson"
        parameters:
          lambda: 100.0
      severity:
        model: "lognormal"
        parameters:
          median: 100
          sigma: 1.0
    """
    
    # Run without chain
    res_base = run_monte_carlo(base_yaml, n_runs=100, seed=42)
    base_mean = res_base.metrics.eal / 100.0 # roughly lambda (ignoring severity for now, using eal?)
    # Wait EAL is loss. We need frequency count. metrics doesn't expose freq count directly.
    # But simulation result has no direct frequency metric exposed in Metrics object?
    # Actually metrics has no frequency stats.
    # However, if severity median=100, EAL ~= frequency * 100. 
    # So EAL_base ~= 100 * 100 = 10000.
    
    base_eal = res_base.metrics.eal
    assert base_eal > 0
    
    # Scenario with Attack Chain (0.5 probability)
    # Construct distinct YAML to avoid brittle replacement issues
    chain_yaml = """
    crml_scenario: "1.0"
    meta:
      name: "Test Chain"
    scenario:
      frequency:
        model: "poisson"
        parameters:
          lambda: 100.0
      severity:
        model: "lognormal"
        parameters:
          median: 100
          sigma: 1.0
      attack_chain:
        stages:
          - name: "Filter"
            probability: 0.5
    """
            
    res_chain = run_monte_carlo(chain_yaml, n_runs=100, seed=42)
    assert res_chain.success, f"Simulation failed: {res_chain.errors}"
    
    chain_eal = res_chain.metrics.eal
    
    # Expect roughly 50% reduction
    ratio = chain_eal / base_eal
    assert 0.4 < ratio < 0.6, f"Expected ~0.5 ratio, got {ratio}"

def test_attack_chain_with_controls():
    """Test that controls mitigate the attack chain further."""
    
    yaml_with_controls = """
    crml_scenario: "1.0"
    meta:
      name: "Test Chain Controls"
    scenario:
      frequency:
        model: "poisson"
        parameters:
          lambda: 100.0
      severity:
        model: "lognormal"
        parameters:
          median: 100
          sigma: 1.0
      attack_chain:
        stages:
          - name: "Stage 1"
            probability: 1.0
            controls: ["nist:ac-1"]
    """
    
    # Run with control map where nist:ac-1 has 0.9 effectiveness
    # Residual = 1.0 * (1 - 0.9) = 0.1
    controls = {"nist:ac-1": 0.9}
    
    res = run_monte_carlo(
        yaml_with_controls, 
        n_runs=100, 
        seed=42, 
        control_effectiveness_map=controls
    )
    
    # Base expected EAL ~ 10000. With 0.1 factor -> ~1000.
    # Checking against a run without controls (eff=0)
    res_no_controls = run_monte_carlo(
        yaml_with_controls, 
        n_runs=100, 
        seed=42
        # No controls map -> assumes 0 effectiveness
    )
    
    ratio = res.metrics.eal / res_no_controls.metrics.eal
    assert 0.05 < ratio < 0.15, f"Expected ~0.1 ratio from 0.9 effectiveness, got {ratio}"
