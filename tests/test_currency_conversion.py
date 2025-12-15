import pytest
import numpy as np
from crml.runtime import run_simulation, convert_currency, DEFAULT_FX_RATES


def test_single_currency_usd():
    """Test basic single currency model in USD."""
    
    model = """
crml: "1.1"
meta:
  name: "usd-test"
model:
  frequency:
    model: poisson
    parameters:
      lambda: 1.0
  severity:
    model: lognormal
    parameters:
      median: 100000
      currency: USD
      sigma: 1.2
"""
    
    result = run_simulation(model, n_runs=10000, seed=42)
    assert result["success"] is True
    assert result["metadata"]["currency_code"] == "USD"
    assert result["metrics"]["eal"] > 0


def test_multi_currency_mixture():
    """Test mixture model with multiple currencies."""
    
    model = """
crml: "1.1"
meta:
  name: "multi-currency-test"
model:
  frequency:
    model: poisson
    parameters:
      lambda: 1.0
  severity:
    model: mixture
    components:
      - lognormal:
          weight: 0.5
          median: 100000
          currency: USD
          sigma: 1.2
      - lognormal:
          weight: 0.5
          median: 100000
          currency: EUR
          sigma: 1.2
"""
    
    fx_config = {
        "base_currency": "USD",
        "output_currency": "USD",
        "rates": DEFAULT_FX_RATES
    }
    
    result = run_simulation(model, n_runs=10000, seed=42, fx_config=fx_config)
    assert result["success"] is True
    assert result["metadata"]["currency_code"] == "USD"


def test_fx_config_conversion():
    """Test that FX config properly converts output currency."""
    
    model = """
crml: "1.1"
meta:
  name: "fx-test"
model:
  frequency:
    model: poisson
    parameters:
      lambda: 1.0
  severity:
    model: lognormal
    parameters:
      median: 100000
      currency: USD
      sigma: 1.0
"""
    
    # Run in USD
    fx_usd = {
        "base_currency": "USD",
        "output_currency": "USD",
        "rates": DEFAULT_FX_RATES
    }
    result_usd = run_simulation(model, n_runs=50000, seed=42, fx_config=fx_usd)
    
    # Run in EUR
    fx_eur = {
        "base_currency": "USD",
        "output_currency": "EUR",
        "rates": DEFAULT_FX_RATES
    }
    result_eur = run_simulation(model, n_runs=50000, seed=42, fx_config=fx_eur)
    
    assert result_usd["success"] is True
    assert result_eur["success"] is True
    
    # EAL in EUR should be EAL in USD divided by EUR rate
    eal_usd = result_usd["metrics"]["eal"]
    eal_eur = result_eur["metrics"]["eal"]
    eur_rate = DEFAULT_FX_RATES["EUR"]
    
    expected_eal_eur = eal_usd / eur_rate
    relative_diff = abs(eal_eur - expected_eal_eur) / expected_eal_eur
    assert relative_diff < 0.02, f"Currency conversion incorrect: {eal_eur} vs {expected_eal_eur}"


def test_convert_currency_function():
    """Test the convert_currency utility function."""
    
    # USD to EUR
    usd_amount = 100000
    eur_amount = convert_currency(usd_amount, "USD", "EUR", {"rates": DEFAULT_FX_RATES})
    eur_rate = DEFAULT_FX_RATES["EUR"]
    expected = usd_amount / eur_rate
    assert abs(eur_amount - expected) < 0.01
    
    # EUR to USD
    eur_amount = 100000
    usd_amount = convert_currency(eur_amount, "EUR", "USD", {"rates": DEFAULT_FX_RATES})
    expected = eur_amount * eur_rate
    assert abs(usd_amount - expected) < 0.01
    
    # Same currency (no conversion)
    usd_amount = 100000
    result = convert_currency(usd_amount, "USD", "USD", {"rates": DEFAULT_FX_RATES})
    assert result == usd_amount


def test_currency_normalization():
    """Test that different input currencies are properly normalized."""
    
    # Model with EUR input
    model_eur = """
crml: "1.1"
meta:
  name: "eur-input"
model:
  frequency:
    model: poisson
    parameters:
      lambda: 1.0
  severity:
    model: lognormal
    parameters:
      median: 100000
      currency: EUR
      sigma: 1.0
"""
    
    # Model with USD input (equivalent value)
    eur_rate = DEFAULT_FX_RATES["EUR"]
    usd_equivalent = 100000 * eur_rate
    
    model_usd = f"""
crml: "1.1"
meta:
  name: "usd-input"
model:
  frequency:
    model: poisson
    parameters:
      lambda: 1.0
  severity:
    model: lognormal
    parameters:
      median: {usd_equivalent}
      currency: USD
      sigma: 1.0
"""
    
    fx_config = {
        "base_currency": "USD",
        "output_currency": "USD",
        "rates": DEFAULT_FX_RATES
    }
    
    result_eur = run_simulation(model_eur, n_runs=50000, seed=42, fx_config=fx_config)
    result_usd = run_simulation(model_usd, n_runs=50000, seed=42, fx_config=fx_config)
    
    assert result_eur["success"] is True
    assert result_usd["success"] is True
    
    # Results should be very close since we normalized the inputs
    eal_eur = result_eur["metrics"]["eal"]
    eal_usd = result_usd["metrics"]["eal"]
    relative_diff = abs(eal_eur - eal_usd) / max(eal_eur, eal_usd)
    assert relative_diff < 0.03, f"Normalized results don't match: {eal_eur} vs {eal_usd}"


def test_supported_currencies():
    """Test that all documented currencies are supported."""
    
    supported = ["USD", "EUR", "GBP", "CHF", "JPY", "CNY", "CAD", "AUD", 
                 "INR", "BRL", "PKR", "MXN", "KRW", "SGD", "HKD"]
    
    for currency in supported:
        assert currency in DEFAULT_FX_RATES, f"{currency} not in DEFAULT_FX_RATES"
        
        model = f"""
crml: "1.1"
meta:
  name: "test-{currency.lower()}"
model:
  frequency:
    model: poisson
    parameters:
      lambda: 1.0
  severity:
    model: lognormal
    parameters:
      median: 100000
      currency: {currency}
      sigma: 1.0
"""
        
        result = run_simulation(model, n_runs=1000, seed=42)
        assert result["success"] is True, f"Failed for currency {currency}"
