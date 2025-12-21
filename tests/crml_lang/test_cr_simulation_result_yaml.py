from __future__ import annotations

from crml_lang import CRSimulationResult


def _minimal_result_dict() -> dict:
    return {
        "crml_simulation_result": "1.0",
        "result": {
            "success": True,
            "errors": [],
            "warnings": [],
            "engine": {"name": "unit-test-engine", "version": "0.0"},
            "run": {"runs": 10, "seed": 123},
            "inputs": {"model_name": "test"},
            "units": {"currency": {"code": "USD"}},
            "results": {
                "measures": [{"id": "eal", "value": 123.4}],
                "artifacts": [],
            },
        },
    }


def test_cr_simulation_result_yaml_str_round_trip() -> None:
    env = CRSimulationResult.model_validate(_minimal_result_dict())

    yaml_text = env.dump_to_yaml_str(sort_keys=False)
    round_tripped = CRSimulationResult.load_from_yaml_str(yaml_text)

    assert round_tripped.model_dump() == env.model_dump()


def test_cr_simulation_result_yaml_file_round_trip(tmp_path) -> None:
    env = CRSimulationResult.model_validate(_minimal_result_dict())

    out_path = tmp_path / "result.yaml"
    env.dump_to_yaml(str(out_path), sort_keys=False)

    round_tripped = CRSimulationResult.load_from_yaml(str(out_path))
    assert round_tripped.model_dump() == env.model_dump()
