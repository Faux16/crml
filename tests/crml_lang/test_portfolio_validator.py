import pytest

from crml_lang import validate_portfolio


def test_validate_portfolio_ok_mixture():
    portfolio_yaml = """
    crml_portfolio: "1.0"
    meta: {name: "Example portfolio"}
    portfolio:
      semantics:
        method: mixture
      scenarios:
        - id: phishing
          path: phishing.yaml
          weight: 0.7
        - id: ransomware
          path: ransomware.yaml
          weight: 0.3
      relationships:
        - type: correlation
          between: [phishing, ransomware]
          value: 0.2
    """

    report = validate_portfolio(portfolio_yaml, source_kind="yaml")
    assert report.ok is True


def test_validate_portfolio_weights_must_sum_to_one():
    portfolio_yaml = """
    crml_portfolio: "1.0"
    meta: {name: "Bad weights"}
    portfolio:
      semantics:
        method: mixture
      scenarios:
        - id: a
          path: a.yaml
          weight: 0.7
        - id: b
          path: b.yaml
          weight: 0.4
    """

    report = validate_portfolio(portfolio_yaml, source_kind="yaml")
    assert report.ok is False
    assert any("weights must sum to 1.0" in e.message for e in report.errors)


def test_validate_portfolio_missing_weight_is_error_for_mixture():
    portfolio_yaml = """
    crml_portfolio: "1.0"
    meta: {name: "Missing weight"}
    portfolio:
      semantics:
        method: mixture
      scenarios:
        - id: a
          path: a.yaml
          weight: 1.0
        - id: b
          path: b.yaml
    """

    report = validate_portfolio(portfolio_yaml, source_kind="yaml")
    assert report.ok is False
    assert any("must define 'weight'" in e.message for e in report.errors)


def test_validate_portfolio_relationship_references_must_exist():
    portfolio_yaml = """
    crml_portfolio: "1.0"
    meta: {name: "Bad relationship"}
    portfolio:
      semantics:
        method: sum
      scenarios:
        - id: a
          path: a.yaml
      relationships:
        - type: correlation
          between: [a, missing]
          value: 0.2
    """

    report = validate_portfolio(portfolio_yaml, source_kind="yaml")
    assert report.ok is False
    assert any("Unknown scenario id" in e.message for e in report.errors)


def test_validate_portfolio_warns_binding_for_per_organization_basis(tmp_path):
    scenario = tmp_path / "phishing.yaml"
    scenario.write_text(
        """
crml_scenario: "1.0"
meta: {name: "phishing"}
scenario:
  frequency:
    basis: per_organization_per_year
    model: poisson
    parameters: {lambda: 0.1}
  severity:
    model: lognormal
    parameters: {median: 1000, currency: USD, sigma: 1.0}
""".lstrip(),
        encoding="utf-8",
    )

    portfolio = tmp_path / "portfolio.yaml"
    portfolio.write_text(
        f"""
crml_portfolio: "1.0"
meta: {{name: "p"}}
portfolio:
  assets:
    - name: employees
      cardinality: 100
  semantics:
    method: sum
    constraints:
      require_paths_exist: true
      validate_scenarios: true
  scenarios:
    - id: phishing
      path: {scenario.name}
      binding:
        applies_to_assets: [employees]
""".lstrip(),
        encoding="utf-8",
    )

    report = validate_portfolio(str(portfolio), source_kind="path")
    assert report.ok is True
    assert any("per_organization_per_year" in w.message and "does not affect frequency" in w.message for w in report.warnings)


def test_validate_portfolio_warns_zero_exposure_for_per_asset_basis(tmp_path):
    scenario = tmp_path / "endpoint-risk.yaml"
    scenario.write_text(
        """
crml_scenario: "1.0"
meta: {name: "endpoint-risk"}
scenario:
  frequency:
    basis: per_asset_unit_per_year
    model: poisson
    parameters: {lambda: 0.01}
  severity:
    model: lognormal
    parameters: {median: 500, currency: USD, sigma: 1.2}
""".lstrip(),
        encoding="utf-8",
    )

    portfolio = tmp_path / "portfolio.yaml"
    portfolio.write_text(
        f"""
crml_portfolio: "1.0"
meta: {{name: "p"}}
portfolio:
  assets:
    - name: endpoints
      cardinality: 500
  semantics:
    method: sum
    constraints:
      require_paths_exist: true
      validate_scenarios: true
  scenarios:
    - id: endpoint-risk
      path: {scenario.name}
      binding:
        applies_to_assets: []
""".lstrip(),
        encoding="utf-8",
    )

    report = validate_portfolio(str(portfolio), source_kind="path")
    assert report.ok is True
    assert any("per_asset_unit_per_year" in w.message and "E=0" in w.message for w in report.warnings)
