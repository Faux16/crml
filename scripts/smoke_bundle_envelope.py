import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "crml_engine" / "src"))
sys.path.insert(0, str(REPO / "crml_lang" / "src"))

from crml_engine.runtime import run_simulation_envelope  # noqa: E402


def main() -> int:
    bundle_path = REPO / "examples" / "portfolio_bundles" / "portfolio-bundle-documented.yaml"
    yaml_text = bundle_path.read_text(encoding="utf-8")

    env = run_simulation_envelope(
        yaml_text,
        n_runs=10_000,
        seed=123,
        fx_config={"base_currency": "USD", "output_currency": "EUR", "rates": None},
    )

    payload = env.model_dump()
    measures = payload["result"]["results"]["measures"]
    artifacts = payload["result"]["results"]["artifacts"]

    measure_by_id: dict[str, list[dict]] = {}
    for measure in measures:
        measure_by_id.setdefault(measure["id"], []).append(measure)

    def get_measure(measure_id: str):
        ms = measure_by_id.get(measure_id, [])
        return ms[0]["value"] if ms else None

    import math
    var_95 = None
    for measure in measure_by_id.get("loss.var", []):
        level = measure.get("parameters", {}).get("level")
        if level is not None and math.isclose(level, 0.95, rel_tol=1e-9):
            var_95 = measure.get("value")
            break

    hist = next(
        (a for a in artifacts if a.get("kind") == "histogram" and a.get("id") == "loss.annual"),
        None,
    )

    out = {
        "success": payload["result"]["success"],
        "currency": payload["result"].get("units", {}).get("currency"),
        "eal": get_measure("loss.eal"),
        "var_95": var_95,
        "min": get_measure("loss.min"),
        "max": get_measure("loss.max"),
        "hist_edges_unique": len(set(hist["bin_edges"])) if hist else None,
        "hist_edges_first": hist["bin_edges"][:5] if hist else None,
        "hist_counts_sum": sum(hist["counts"]) if hist else None,
    }

    print(json.dumps(out, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
