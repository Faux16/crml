from __future__ import annotations

from crml_lang import validate_portfolio


def test_portfolio_requires_explicit_controls_for_scenario_controls(tmp_path) -> None:
    scenario_path = tmp_path / "scenario.yaml"
    scenario_path.write_text(
        """
crml_scenario: "1.2"
meta:
  name: "Threat scenario"
scenario:
  controls:
    - "iso27001:2022:A.5.1"
  frequency:
    basis: per_organization_per_year
    model: poisson
    parameters: {lambda: 0.5}
  severity:
    model: lognormal
    parameters: {mu: 10, sigma: 1}
""".lstrip(),
        encoding="utf-8",
    )

    portfolio_path = tmp_path / "portfolio.yaml"
    portfolio_path.write_text(
        f"""
crml_portfolio: "1.0"
meta:
  name: "Org portfolio"
portfolio:
  semantics:
    method: sum
    constraints:
      require_paths_exist: true
      validate_scenarios: true
  controls: []
  scenarios:
    - id: s1
      path: {scenario_path.name}
""".lstrip(),
        encoding="utf-8",
    )

    report = validate_portfolio(str(portfolio_path), source_kind="path")
    assert report.ok is False
    assert any("portfolio.controls is missing or empty" in e.message for e in report.errors)


def test_portfolio_controls_can_set_implementation_effectiveness(tmp_path) -> None:
    scenario_path = tmp_path / "scenario.yaml"
    scenario_path.write_text(
        """
crml_scenario: "1.2"
meta:
  name: "Threat scenario"
scenario:
  controls:
    - "iso27001:2022:A.5.1"
  frequency:
    basis: per_organization_per_year
    model: poisson
    parameters: {lambda: 0.5}
  severity:
    model: lognormal
    parameters: {mu: 10, sigma: 1}
""".lstrip(),
        encoding="utf-8",
    )

    portfolio_path = tmp_path / "portfolio.yaml"
    portfolio_path.write_text(
        f"""
crml_portfolio: "1.0"
meta:
  name: "Org portfolio"
portfolio:
  semantics:
    method: sum
    constraints:
      require_paths_exist: true
      validate_scenarios: true
  controls:
    - id: "iso27001:2022:A.5.1"
      implementation_effectiveness: 0.0
  scenarios:
    - id: s1
      path: {scenario_path.name}
""".lstrip(),
        encoding="utf-8",
    )

    report = validate_portfolio(str(portfolio_path), source_kind="path")
    assert report.ok is True


def test_scenario_control_objects_are_supported_for_mapping(tmp_path) -> None:
    scenario_path = tmp_path / "scenario.yaml"
    scenario_path.write_text(
        """
crml_scenario: "1.2"
meta:
  name: "Threat scenario"
scenario:
  controls:
    - id: "iso27001:2022:A.5.1"
      implementation_effectiveness: 0.6
      coverage: {value: 0.5, basis: applications}
  frequency:
    basis: per_organization_per_year
    model: poisson
    parameters: {lambda: 0.5}
  severity:
    model: lognormal
    parameters: {mu: 10, sigma: 1}
""".lstrip(),
        encoding="utf-8",
    )

    portfolio_path = tmp_path / "portfolio.yaml"
    portfolio_path.write_text(
        f"""
crml_portfolio: "1.0"
meta:
  name: "Org portfolio"
portfolio:
  semantics:
    method: sum
    constraints:
      require_paths_exist: true
      validate_scenarios: true
  controls:
    - id: "iso27001:2022:A.5.1"
      implementation_effectiveness: 0.0
      coverage: {{value: 1.0, basis: applications}}
  scenarios:
    - id: s1
      path: {scenario_path.name}
""".lstrip(),
        encoding="utf-8",
    )

    report = validate_portfolio(str(portfolio_path), source_kind="path")
    assert report.ok is True
