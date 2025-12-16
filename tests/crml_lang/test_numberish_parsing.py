from crml_lang import CRPortfolio, CRScenario


def test_numberish_strings_parse_to_numbers():
    yaml_text = """
crml_scenario: "1.2"
meta:
  name: "readable-numbers"
scenario:
  frequency:
    basis: per_organization_per_year
    model: poisson
    parameters:
      lambda: "0.5"
  severity:
    model: lognormal
    parameters:
      mu: "10"
      sigma: "1 234.5"
"""

    scenario = CRScenario.load_from_yaml_str(yaml_text)

    assert isinstance(scenario.scenario.frequency.parameters.lambda_, float)
    assert scenario.scenario.frequency.parameters.lambda_ == 0.5

    assert isinstance(scenario.scenario.severity.parameters.mu, float)
    assert scenario.scenario.severity.parameters.mu == 10.0

    assert isinstance(scenario.scenario.severity.parameters.sigma, float)
    assert scenario.scenario.severity.parameters.sigma == 1234.5


def test_cardinality_must_be_natural_integer():
    # 0 is not allowed
    yaml_zero = """
crml_portfolio: "1.0"
meta:
  name: "bad-cardinality-zero"
portfolio:
  assets:
    - name: "Servers"
      cardinality: 0
  scenarios:
    - id: "s1"
      path: "scenario.yaml"
  semantics:
    method: sum
"""
    try:
        CRPortfolio.load_from_yaml_str(yaml_zero)
        assert False, "expected cardinality=0 to be rejected"
    except Exception:
        pass

    # Floats are not allowed
    yaml_float = """
crml_portfolio: "1.0"
meta:
  name: "bad-cardinality-float"
portfolio:
  assets:
    - name: "Servers"
      cardinality: 1.5
  scenarios:
    - id: "s1"
      path: "scenario.yaml"
  semantics:
    method: sum
"""
    try:
        CRPortfolio.load_from_yaml_str(yaml_float)
        assert False, "expected float cardinality to be rejected"
    except Exception:
        pass

    # Decimal-looking strings are not allowed
    yaml_decimal_str = """
crml_portfolio: "1.0"
meta:
  name: "bad-cardinality-decimal-string"
portfolio:
  assets:
    - name: "Servers"
      cardinality: "10.0"
  scenarios:
    - id: "s1"
      path: "scenario.yaml"
  semantics:
    method: sum
"""
    try:
        CRPortfolio.load_from_yaml_str(yaml_decimal_str)
        assert False, "expected decimal string cardinality to be rejected"
    except Exception:
        pass


def test_percent_strings_allowed_only_for_probability_like_fields():
    # p should accept percent strings
    yaml_ok = """
crml_scenario: "1.2"
meta:
  name: "percent-ok"
scenario:
  frequency:
    basis: per_organization_per_year
    model: negbin
    parameters:
      r: 10
      p: "25%"
  severity:
    model: lognormal
    parameters:
      mu: 10
      sigma: 1
"""
    scenario = CRScenario.load_from_yaml_str(yaml_ok)
    assert scenario.scenario.frequency.parameters.p == 0.25

    # median should NOT accept percent strings (absolute value field)
    yaml_bad = """
crml_scenario: "1.2"
meta:
  name: "percent-bad"
scenario:
  frequency:
    basis: per_organization_per_year
    model: poisson
    parameters:
      lambda: 0.5
  severity:
    model: lognormal
    parameters:
      median: "25%"
      sigma: 1
"""

    try:
      CRScenario.load_from_yaml_str(yaml_bad)
        assert False, "expected percent string in severity.median to be rejected"
    except Exception:
        pass
