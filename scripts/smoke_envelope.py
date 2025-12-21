import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "crml_engine" / "src"))
sys.path.insert(0, str(REPO / "crml_lang" / "src"))

from crml_engine.runtime import run_simulation_envelope  # noqa: E402

YAML = """crml_scenario: \"1.0\"
meta:
  name: \"web-smoke\"
scenario:
  frequency:
    basis: per_organization_per_year
    model: poisson
    parameters: {lambda: 0.5}
  severity:
    model: lognormal
    parameters: {mu: 10.0, sigma: 1.0}
"""


env = run_simulation_envelope(
    YAML,
    n_runs=200,
    seed=123,
    fx_config={"base_currency": "USD", "output_currency": "EUR", "rates": None},
)

payload = json.loads(env.model_dump_json())
print(
  json.dumps(
    {
      "crml_simulation_result": payload["crml_simulation_result"],
      "success": payload["result"]["success"],
      "started_at": payload["result"].get("run", {}).get("started_at"),
      "measures": len(payload["result"]["results"]["measures"]),
      "artifacts": len(payload["result"]["results"]["artifacts"]),
    }
  )
)
