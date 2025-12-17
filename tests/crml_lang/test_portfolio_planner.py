from __future__ import annotations

from crml_engine.pipeline import plan_portfolio


def test_plan_portfolio_expands_per_asset_cardinality(tmp_path) -> None:
    scenario_path = tmp_path / "scenario.yaml"
    scenario_path.write_text(
        """
crml_scenario: "1.0"
meta:
  name: "Per-asset scenario"
scenario:
  frequency:
    basis: per_asset_unit_per_year
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
  assets:
    - name: a1
      cardinality: 10
    - name: a2
      cardinality: 5
  semantics:
    method: sum
  scenarios:
    - id: s1
      path: {scenario_path.name}
      binding:
        applies_to_assets: [a1, a2]
""".lstrip(),
        encoding="utf-8",
    )

    report = plan_portfolio(str(portfolio_path), source_kind="path")
    assert report.ok is True
    assert report.plan is not None
    assert report.plan.scenarios[0].cardinality == 15
    assert report.plan.scenarios[0].applies_to_assets == ["a1", "a2"]


def test_plan_portfolio_defaults_binding_to_all_assets(tmp_path) -> None:
    scenario_path = tmp_path / "scenario.yaml"
    scenario_path.write_text(
        """
crml_scenario: "1.0"
meta:
  name: "Per-asset scenario"
scenario:
  frequency:
    basis: per_asset_unit_per_year
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
  assets:
    - name: a1
      cardinality: 2
    - name: a2
      cardinality: 3
  semantics:
    method: sum
  scenarios:
    - id: s1
      path: {scenario_path.name}
""".lstrip(),
        encoding="utf-8",
    )

    report = plan_portfolio(str(portfolio_path), source_kind="path")
    assert report.ok is True
    assert report.plan is not None
    assert report.plan.scenarios[0].cardinality == 5
    assert set(report.plan.scenarios[0].applies_to_assets) == {"a1", "a2"}


def test_plan_portfolio_resolves_controls_with_precedence_and_factors(tmp_path) -> None:
    scenario_path = tmp_path / "scenario.yaml"
    scenario_path.write_text(
        """
crml_scenario: "1.0"
meta:
  name: "Threat scenario"
scenario:
  controls:
    - id: "iso27001:2022:A.5.1"
      implementation_effectiveness: 0.5
      potency: 0.2
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

    assessment_path = tmp_path / "assessment.yaml"
    assessment_path.write_text(
        """
crml_control_assessment: "1.0"
meta:
  name: "Org assessment"
assessment:
  framework: "Org"
  assessments:
    - id: "iso27001:2022:A.5.1"
      implementation_effectiveness: 0.2
      coverage: {value: 0.8, basis: applications}
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
  control_assessments:
    - {assessment_path.name}
  controls:
    - id: "iso27001:2022:A.5.1"
      implementation_effectiveness: 0.6
      coverage: {{value: 1.0, basis: applications}}
  scenarios:
    - id: s1
      path: {scenario_path.name}
""".lstrip(),
        encoding="utf-8",
    )

    report = plan_portfolio(str(portfolio_path), source_kind="path")
    assert report.ok is True
    assert report.plan is not None

    ctrl = report.plan.scenarios[0].controls[0]
    # Portfolio overrides assessment for inventory values.
    assert ctrl.inventory_implementation_effectiveness == 0.6
    assert ctrl.inventory_coverage_value == 1.0

    # Scenario provides multiplicative applicability factors.
    assert ctrl.scenario_implementation_effectiveness_factor == 0.5
    assert ctrl.scenario_coverage_factor == 0.5
    assert ctrl.scenario_potency_factor == 0.2

    assert ctrl.combined_implementation_effectiveness == 0.06
    assert ctrl.combined_coverage_value == 0.5


def test_plan_portfolio_errors_when_control_not_in_inventory(tmp_path) -> None:
    scenario_path = tmp_path / "scenario.yaml"
    scenario_path.write_text(
        """
crml_scenario: "1.0"
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
  controls: []
  scenarios:
    - id: s1
      path: {scenario_path.name}
""".lstrip(),
        encoding="utf-8",
    )

    report = plan_portfolio(str(portfolio_path), source_kind="path")
    assert report.ok is False
    assert any("no inventory/assessment data" in e.message for e in report.errors)


def test_plan_portfolio_resolves_control_copula_to_matrix(tmp_path) -> None:
    scenario_path = tmp_path / "scenario.yaml"
    scenario_path.write_text(
        """
crml_scenario: "1.0"
meta:
  name: "Threat scenario"
scenario:
  controls:
    - "cap:edr"
    - "cap:mfa"
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

    # Inventory in portfolio (reliability + affects)
    portfolio_path = tmp_path / "portfolio.yaml"
    portfolio_path.write_text(
        f"""
crml_portfolio: "1.0"
meta:
  name: "Org portfolio"
portfolio:
  semantics:
    method: sum
  controls:
    - id: "cap:edr"
      implementation_effectiveness: 0.6
      coverage: {{value: 1.0, basis: applications}}
      reliability: 0.8
      affects: frequency
    - id: "cap:mfa"
      implementation_effectiveness: 0.7
      coverage: {{value: 0.9, basis: applications}}
      reliability: 0.9
      affects: both
  dependency:
    copula:
      type: gaussian
      structure: toeplitz
      rho: 0.65
      targets:
        - control:cap:edr:state
        - control:cap:mfa:state
  scenarios:
    - id: s1
      path: {scenario_path.name}
""".lstrip(),
        encoding="utf-8",
    )

    report = plan_portfolio(str(portfolio_path), source_kind="path")
    assert report.ok is True
    assert report.plan is not None
    assert report.plan.dependency is not None
    cop = report.plan.dependency["copula"]
    assert cop["type"] == "gaussian"
    assert cop["targets"] == ["control:cap:edr:state", "control:cap:mfa:state"]
    assert len(cop["matrix"]) == 2
    assert len(cop["matrix"][0]) == 2

    # Planner should also resolve absolute scenario paths.
    assert report.plan.scenarios[0].resolved_path is not None

    # Reliability should be carried through.
    ctrls = report.plan.scenarios[0].controls
    by_id = {c.id: c for c in ctrls}
    assert by_id["cap:edr"].combined_reliability == 0.8
    assert by_id["cap:mfa"].combined_reliability == 0.9
