import pytest
from unittest.mock import patch, MagicMock
import numpy as np
from crml.runtime import run_simulation, DEFAULT_FX_RATES

def test_run_simulation_valid(valid_crml_file):
    # Mock numpy random to make test deterministic if needed, 
    # but for now we just check it runs without error.
    result = run_simulation(valid_crml_file, n_runs=100, seed=123)
    assert isinstance(result, dict)
    assert result["success"] is True

def test_run_simulation_invalid_file(tmp_path):
    p = tmp_path / "invalid.yaml"
    p.write_text("invalid content")
    result = run_simulation(str(p), n_runs=10, seed=123)
    assert result["success"] is False

def test_run_simulation_unsupported_model(tmp_path):
    content = """
crml: "1.1"
model:
  frequency:
    model: unknown_model
  severity:
    model: lognormal
"""
    p = tmp_path / "unsupported.yaml"
    p.write_text(content)
    result = run_simulation(str(p), n_runs=10, seed=123)
    assert result["success"] is False


def test_lognormal_mu_currency_matches_single_losses_with_output_currency_conversion():
    """Regression: providing mu/sigma with a severity currency should match single_losses.

    Prior bug: when output_currency != severity currency, single_losses were converted before
    calibration but user-provided mu was not shifted, producing inflated EAL.
    """
    fx_config = {
        "base_currency": "USD",
        "output_currency": "EUR",
        "rates": DEFAULT_FX_RATES,
    }

    # Loss amounts in USD
    single_losses_model = """
crml: "1.1"
meta:
  name: "single-losses"
model:
  frequency:
    model: poisson
    parameters:
      lambda: 1.0
  severity:
    model: lognormal
    parameters:
      currency: USD
      single_losses:
        - "25 000"
        - "18 000"
        - "45 000"
        - "32 000"
"""

    # Equivalent mu/sigma (ln(median), stddev(ln(losses))) in USD
    mu_sigma_model = """
crml: "1.1"
meta:
  name: "mu-sigma"
model:
  frequency:
    model: poisson
    parameters:
      lambda: 1.0
  severity:
    model: lognormal
    parameters:
      currency: USD
      mu: 10.2532
      sigma: 0.3355
"""

    n_runs = 50000
    seed = 42

    res_single = run_simulation(single_losses_model, n_runs=n_runs, seed=seed, fx_config=fx_config)
    res_mu = run_simulation(mu_sigma_model, n_runs=n_runs, seed=seed, fx_config=fx_config)

    assert res_single["success"] is True
    assert res_mu["success"] is True

    # With same seed and sufficiently large runs, EALs should be very close.
    # Allow small Monte Carlo noise.
    eal_single = res_single["metrics"]["eal"]
    eal_mu = res_mu["metrics"]["eal"]
    assert abs(eal_single - eal_mu) / max(1.0, eal_single) < 0.02
