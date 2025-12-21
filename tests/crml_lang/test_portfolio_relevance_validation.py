from __future__ import annotations


from crml_lang import validate_portfolio


def test_validate_portfolio_relevance_industry_mismatch_is_error(tmp_path) -> None:
    scenario_path = tmp_path / "scenario.yaml"
    scenario_path.write_text(
        """
crml_scenario: "1.0"
meta:
  name: "Scenario"
  industries: ["finance"]
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
  industries: ["healthcare"]
portfolio:
  semantics:
    method: sum
    constraints:
      validate_relevance: true
  scenarios:
    - id: s1
      path: {scenario_path.name}
""".lstrip(),
        encoding="utf-8",
    )

    report = validate_portfolio(str(portfolio_path), source_kind="path")
    assert report.ok is False
    assert any("not relevant" in e.message for e in report.errors)


def test_validate_portfolio_relevance_control_namespace_must_be_declared(tmp_path) -> None:
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
  regulatory_frameworks: ["cisv8"]
portfolio:
  controls:
    - id: iso27001:2022:A.5.1
      implementation_effectiveness: 0.5
  semantics:
    method: sum
    constraints:
      validate_relevance: true
  scenarios:
    - id: s1
      path: {scenario_path.name}
""".lstrip(),
        encoding="utf-8",
    )

    report = validate_portfolio(str(portfolio_path), source_kind="path")
    assert report.ok is False
    assert any("uses namespace" in e.message for e in report.errors)


def test_validate_portfolio_relevance_infers_frameworks_from_control_catalog(tmp_path) -> None:
    catalog_path = tmp_path / "control-catalog.yaml"
    catalog_path.write_text(
        """
crml_control_catalog: "1.0"
meta:
  name: "Catalog"
catalog:
  name: "Controls"
  controls:
    - id: "cisv8:1.1"
      title: "Inventory and Control of Enterprise Assets"
""".lstrip(),
        encoding="utf-8",
    )

    scenario_path = tmp_path / "scenario.yaml"
    scenario_path.write_text(
        """
crml_scenario: "1.0"
meta:
  name: "Scenario"
  regulatory_frameworks: ["iso27001"]
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
portfolio:
  control_catalogs:
    - {catalog_path.name}
  semantics:
    method: sum
    constraints:
      validate_relevance: true
  scenarios:
    - id: s1
      path: {scenario_path.name}
""".lstrip(),
        encoding="utf-8",
    )

    report = validate_portfolio(str(portfolio_path), source_kind="path")
    assert report.ok is False
    assert any("regulatory frameworks" in e.message for e in report.errors)


def test_validate_portfolio_requires_catalog_when_assessments_used(tmp_path) -> None:
    assessment_path = tmp_path / "control-assessment.yaml"
    assessment_path.write_text(
        """
crml_assessment: "1.0"
meta:
  name: "Assessment"
assessment:
  framework: "Org"
  assessed_at: "2025-12-17T10:15:30Z"
  assessments:
    - id: "org:iam.mfa"
      scf_cmm_level: 3
""".lstrip(),
        encoding="utf-8",
    )

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
portfolio:
  assessments:
    - {assessment_path.name}
  semantics:
    method: sum
  scenarios:
    - id: s1
      path: {scenario_path.name}
""".lstrip(),
        encoding="utf-8",
    )

    report = validate_portfolio(str(portfolio_path), source_kind="path")
    assert report.ok is False
    assert any("control_catalogs" in e.path for e in report.errors)
