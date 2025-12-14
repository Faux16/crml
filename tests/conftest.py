import pytest
import os

@pytest.fixture
def valid_crml_content():
    return """
crml: "1.1"
meta:
  name: "test-model"
  description: "A test model"
model:
  assets:
    cardinality: 100
  frequency:
    model: poisson
    parameters:
      lambda: 0.5
  severity:
    model: lognormal
    parameters:
      mu: 10.0
      sigma: 1.0
"""

@pytest.fixture
def valid_crml_file(tmp_path, valid_crml_content):
    p = tmp_path / "model.yaml"
    p.write_text(valid_crml_content)
    return str(p)
