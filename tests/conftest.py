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
def valid_bundle_content(valid_crml_content: str) -> str:
    # Minimal bundle: portfolio + one inlined scenario.
    # Note: portfolio controls/assessments/relationships are intentionally omitted.
    # The engine can still run, and validators may emit warnings depending on scenario content.
    indented_content = valid_crml_content.rstrip().replace('\n', '\n        ')
    return f"""
crml_portfolio_bundle: "1.0"
portfolio_bundle:
  portfolio:
    crml_portfolio: "1.0"
    meta:
      name: "test-bundle"
    portfolio:
      semantics:
        method: sum
        constraints:
          require_paths_exist: false
          validate_scenarios: false
      assets: []
      scenarios:
        - id: s1
          path: scenario.yaml
  scenarios:
    - id: s1
      scenario:
        {indented_content}
""".lstrip()


@pytest.fixture
def valid_bundle_file(tmp_path, valid_bundle_content: str):
    p = tmp_path / "bundle.yaml"
    p.write_text(valid_bundle_content, encoding="utf-8")
    return str(p)

@pytest.fixture
def valid_crml_file(tmp_path, valid_crml_content):
    p = tmp_path / "model.yaml"
    p.write_text(valid_crml_content)
    return str(p)
