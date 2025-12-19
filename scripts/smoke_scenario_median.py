import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "crml_engine" / "src"))
sys.path.insert(0, str(REPO / "crml_lang" / "src"))

from crml_engine.simulation.engine import run_monte_carlo
from crml_engine.models.fx_model import normalize_fx_config

YAML = """crml_scenario: "1.0"
meta:
  name: "median-test"
scenario:
  frequency:
    basis: per_organization_per_year
    model: poisson
    parameters:
      lambda: 0.8
  severity:
    model: lognormal
    parameters:
      currency: USD
      median: "250 000"
      sigma: 1.1
"""

fx = normalize_fx_config({"base_currency": "USD", "output_currency": "EUR", "rates": None})
res = run_monte_carlo(YAML, n_runs=10000, seed=123, fx_config=fx, raw_data_limit=10000)
print("success", res.success)
print("eal", res.metrics.eal if res.metrics else None)
print("min", res.metrics.min if res.metrics else None)
print("max", res.metrics.max if res.metrics else None)
