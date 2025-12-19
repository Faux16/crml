from __future__ import annotations
import sys
from pathlib import Path
import pytest

# Ensure tests exercise the in-repo packages (not any globally-installed versions).
_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "crml_lang" / "src"))
sys.path.insert(0, str(_REPO_ROOT / "crml_engine" / "src"))

@pytest.fixture
def valid_crml_content():
    return """
crml_scenario: "1.0"
meta:
  name: "test-model"
  description: "A test model"
scenario:
  frequency:
    basis: per_organization_per_year
    model: poisson
    parameters: {lambda: 0.5}
  severity:
    model: lognormal
    parameters: {mu: 10.0, sigma: 1.0}
"""

@pytest.fixture
def valid_crml_file(tmp_path, valid_crml_content):
    p = tmp_path / "model.yaml"
    p.write_text(valid_crml_content)
    return str(p)
