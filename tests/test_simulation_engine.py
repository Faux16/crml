import pytest
import numpy as np
from crml.simulation.frequency import FrequencyEngine
from crml.simulation.severity import SeverityEngine
from crml.simulation.engine import run_monte_carlo
from crml.models.fx_model import FXConfig, DEFAULT_FX_RATES

# --- Frequency Tests ---

def test_frequency_poisson():
    class MockParams:
        lambda_ = 10.0
    
    n_runs = 1000
    cardinality = 1
    counts = FrequencyEngine.generate_frequency('poisson', MockParams(), n_runs, cardinality)
    
    assert len(counts) == n_runs
    assert np.mean(counts) == pytest.approx(10.0, rel=0.1)

def test_frequency_poisson_scaled():
    class MockParams:
        lambda_ = 2.0
    
    n_runs = 1000
    cardinality = 5
    # Total lambda should be 2 * 5 = 10
    counts = FrequencyEngine.generate_frequency('poisson', MockParams(), n_runs, cardinality)
    
    assert np.mean(counts) == pytest.approx(10.0, rel=0.1)

def test_frequency_gamma():
    class MockParams:
        shape = 10.0
        scale = 1.0
        lambda_ = None
        
    n_runs = 1000
    cardinality = 1
    # Mean of Gamma(shape, scale) = shape * scale = 10
    counts = FrequencyEngine.generate_frequency('gamma', MockParams(), n_runs, cardinality)
    
    assert np.mean(counts) == pytest.approx(10.0, rel=0.1)

def test_frequency_hierarchical():
    class MockParams:
        # High variance scenario
        alpha_base = 10.0
        beta_base = 1.0 # scale
        lambda_ = None
        
    n_runs = 5000
    cardinality = 1
    counts = FrequencyEngine.generate_frequency('hierarchical_gamma_poisson', MockParams(), n_runs, cardinality)
    
    # Mean should still conform to Gamma mean (alpha * beta) = 10
    assert np.mean(counts) == pytest.approx(10.0, rel=0.1)
    # Variance should be higher than Poisson(10) which is 10. 
    # Var(N) = E[Var(N|L)] + Var(E[N|L]) = E[L] + Var(L) = 10 + (shape*scale^2) = 10 + 10 = 20
    assert np.var(counts) == pytest.approx(20.0, rel=0.2)


# --- Severity Tests ---

def test_severity_lognormal_calibration():
    fx_config = FXConfig(base_currency="USD", output_currency="USD", rates=DEFAULT_FX_RATES)
    single_losses = ["100", "100", "100", "100"] # Zero variance
    
    mu, sigma = SeverityEngine.calibrate_lognormal_from_single_losses(
        single_losses, "USD", "USD", fx_config
    )
    
    # Median is 100, so mu = ln(100) approx 4.605
    assert mu == pytest.approx(4.605, rel=0.01)
    assert sigma == pytest.approx(0.0, abs=0.001)

def test_severity_generation_lognormal():
    class MockParams:
        mu = 4.605
        sigma = 0.5
        currency = "USD"
        median = None
        single_losses = None
        
    fx_config = FXConfig(base_currency="USD", output_currency="USD", rates=DEFAULT_FX_RATES)
    
    losses = SeverityEngine.generate_severity('lognormal', MockParams(), None, 1000, fx_config)
    assert len(losses) == 1000
    assert np.median(losses) == pytest.approx(100.0, rel=0.1)


# --- Engine Tests ---

def test_full_engine_execution(tmp_path):
    # Minimal valid CRML
    content = """
crml: "1.1"
meta:
  name: "test-model"
model:
  assets:
    - name: "Server"
      cardinality: 1
  frequency:
    model: poisson
    parameters:
      lambda: 5.0
  severity:
    model: lognormal
    parameters:
      median: 1000
      sigma: 1.0
"""
    f = tmp_path / "model.yaml"
    f.write_text(content)
    
    result = run_monte_carlo(str(f), n_runs=100, seed=42)
    
    assert result.success is True
    assert result.metrics.eal > 0
    assert result.metadata.model_name == "test-model"
