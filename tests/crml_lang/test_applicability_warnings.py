from __future__ import annotations


from crml_lang import validate_portfolio
from crml_lang.validators import scenario as scenario_validator


def test_portfolio_warns_when_org_context_missing() -> None:
    portfolio_yaml = """
crml_portfolio: "1.0"
meta:
  name: "Org"
portfolio:
  semantics:
    method: sum
  scenarios:
    - id: s1
      path: scenario.yaml
""".lstrip()

    report = validate_portfolio(portfolio_yaml, source_kind="yaml")
    assert report.ok is True
    assert any("meta.industries is missing/empty" in w.message for w in report.warnings)
    assert any("meta.company_sizes is missing/empty" in w.message for w in report.warnings)
    assert any("meta.locale.regions is missing/empty" in w.message for w in report.warnings)


def test_portfolio_warns_when_org_context_is_all() -> None:
    portfolio_yaml = """
crml_portfolio: "1.0"
meta:
  name: "Org"
  industries: [all]
  company_sizes: [all]
  locale:
    regions: [all]
portfolio:
  semantics:
    method: sum
  scenarios:
    - id: s1
      path: scenario.yaml
""".lstrip()

    report = validate_portfolio(portfolio_yaml, source_kind="yaml")
    assert report.ok is True
    assert any("contains 'all'" in w.message and "industries" in w.path for w in report.warnings)
    assert any("contains 'all'" in w.message and "company_sizes" in w.path for w in report.warnings)
    assert any("contains 'all'/'world'" in w.message for w in report.warnings)


def test_portfolio_warns_when_scenario_has_no_applicability_meta(tmp_path) -> None:
    scenario_path = tmp_path / "scenario.yaml"
    scenario_path.write_text(
        """
crml_scenario: "1.0"
meta:
  name: "Scenario"
scenario:
  frequency:
    basis: per_organization_per_year
    model: poisson
    parameters: {lambda: 1.0}
  severity:
    model: lognormal
    parameters: {median: 1000, sigma: 1.0}
""".lstrip(),
        encoding="utf-8",
    )

    portfolio_path = tmp_path / "portfolio.yaml"
    portfolio_path.write_text(
        f"""
crml_portfolio: "1.0"
meta:
  name: "Org"
  industries: [financial-services]
  company_sizes: [micro]
  locale:
    regions: [europe]
portfolio:
  semantics:
    method: sum
    constraints:
      validate_scenarios: true
      require_paths_exist: true
  scenarios:
    - id: s1
      path: {scenario_path.name}
""".lstrip(),
        encoding="utf-8",
    )

    report = validate_portfolio(str(portfolio_path), source_kind="path")
    assert report.ok is True
    assert any("Scenario has no applicability metadata" in w.message for w in report.warnings)


def test_scenario_validator_warns_when_no_applicability_meta() -> None:
    scenario_yaml = """
crml_scenario: "1.0"
meta:
  name: "Scenario"
scenario:
  frequency:
    basis: per_organization_per_year
    model: poisson
    parameters: {lambda: 1.0}
  severity:
    model: lognormal
    parameters: {median: 1000, sigma: 1.0}
""".lstrip()

    report = scenario_validator.validate(scenario_yaml, source_kind="yaml")
    assert report.ok is True
    assert any("Scenario applicability metadata is missing" in w.message for w in report.warnings)
