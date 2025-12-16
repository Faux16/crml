from crml_lang import CRScenario


def test_dump_to_yaml_str_preserves_alias_lambda(valid_crml_content):
    scenario = CRScenario.load_from_yaml_str(valid_crml_content)
    yaml_text = scenario.dump_to_yaml_str(sort_keys=False)

    # FrequencyParameters uses `lambda_` internally but must serialize as `lambda`
    assert "lambda:" in yaml_text
    assert "lambda_:" not in yaml_text


def test_dump_to_yaml_file_round_trip(tmp_path, valid_crml_content):
    scenario = CRScenario.load_from_yaml_str(valid_crml_content)

    out_path = tmp_path / "out.yaml"
    scenario.dump_to_yaml(str(out_path), sort_keys=False)

    round_tripped = CRScenario.load_from_yaml(str(out_path))
    assert round_tripped.crml_scenario == scenario.crml_scenario
    assert round_tripped.meta.name == scenario.meta.name
