from crml_lang import CRScenario, load_from_yaml, load_from_yaml_str


def test_load_from_yaml_path(valid_crml_file: str) -> None:
    scenario = CRScenario.load_from_yaml(valid_crml_file)

    assert scenario.crml_scenario == "1.0"
    assert scenario.meta.name == "test-model"
    assert scenario.scenario.frequency.basis == "per_organization_per_year"
    assert scenario.scenario.frequency.model == "poisson"


def test_load_from_yaml_str(valid_crml_content: str) -> None:
    scenario = CRScenario.load_from_yaml_str(valid_crml_content)

    assert scenario.crml_scenario == "1.0"
    assert scenario.meta.name == "test-model"
    assert scenario.scenario.severity.model == "lognormal"


def test_module_level_helpers_match_methods(valid_crml_file: str, valid_crml_content: str) -> None:
    m1 = load_from_yaml(valid_crml_file)
    m2 = CRScenario.load_from_yaml(valid_crml_file)
    assert m1.model_dump() == m2.model_dump()

    s1 = load_from_yaml_str(valid_crml_content)
    s2 = CRScenario.load_from_yaml_str(valid_crml_content)
    assert s1.model_dump() == s2.model_dump()
