from crml.api import CRModel


def test_numberish_strings_parse_to_numbers():
    yaml_text = """
crml: "1.1"
meta:
  name: "readable-numbers"
model:
  assets:
    - name: "Servers"
      cardinality: "10 000"
  frequency:
    model: poisson
    parameters:
      lambda: "0.5"
  severity:
    model: lognormal
    parameters:
      mu: "10"
      sigma: "1 234.5"
"""

    model = CRModel.load_from_yaml_str(yaml_text)

    assert isinstance(model.model.assets[0].cardinality, int)
    assert model.model.assets[0].cardinality == 10000

    assert isinstance(model.model.frequency.parameters.lambda_, float)
    assert model.model.frequency.parameters.lambda_ == 0.5

    assert isinstance(model.model.severity.parameters.mu, float)
    assert model.model.severity.parameters.mu == 10.0

    assert isinstance(model.model.severity.parameters.sigma, float)
    assert model.model.severity.parameters.sigma == 1234.5


def test_cardinality_must_be_natural_integer():
    # 0 is not allowed
    yaml_zero = """
crml: "1.1"
meta:
  name: "bad-cardinality-zero"
model:
  assets:
    - name: "Servers"
      cardinality: 0
  frequency:
    model: poisson
    parameters:
      lambda: 0.5
  severity:
    model: lognormal
    parameters:
      mu: 10
      sigma: 1
"""
    try:
        CRModel.load_from_yaml_str(yaml_zero)
        assert False, "expected cardinality=0 to be rejected"
    except Exception:
        pass

    # Floats are not allowed
    yaml_float = """
crml: "1.1"
meta:
  name: "bad-cardinality-float"
model:
  assets:
    - name: "Servers"
      cardinality: 1.5
  frequency:
    model: poisson
    parameters:
      lambda: 0.5
  severity:
    model: lognormal
    parameters:
      mu: 10
      sigma: 1
"""
    try:
        CRModel.load_from_yaml_str(yaml_float)
        assert False, "expected float cardinality to be rejected"
    except Exception:
        pass

    # Decimal-looking strings are not allowed
    yaml_decimal_str = """
crml: "1.1"
meta:
  name: "bad-cardinality-decimal-string"
model:
  assets:
    - name: "Servers"
      cardinality: "10.0"
  frequency:
    model: poisson
    parameters:
      lambda: 0.5
  severity:
    model: lognormal
    parameters:
      mu: 10
      sigma: 1
"""
    try:
        CRModel.load_from_yaml_str(yaml_decimal_str)
        assert False, "expected decimal string cardinality to be rejected"
    except Exception:
        pass


def test_percent_strings_allowed_only_for_probability_like_fields():
    # p should accept percent strings
    yaml_ok = """
crml: "1.1"
meta:
  name: "percent-ok"
model:
  assets:
    - name: "Servers"
      cardinality: 1
  frequency:
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
    model = CRModel.load_from_yaml_str(yaml_ok)
    assert model.model.frequency.parameters.p == 0.25

    # median should NOT accept percent strings (absolute value field)
    yaml_bad = """
crml: "1.1"
meta:
  name: "percent-bad"
model:
  assets:
    - name: "Servers"
      cardinality: 1
  frequency:
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
        CRModel.load_from_yaml_str(yaml_bad)
        assert False, "expected percent string in severity.median to be rejected"
    except Exception:
        pass
