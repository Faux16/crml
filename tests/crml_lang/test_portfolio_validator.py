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
