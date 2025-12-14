import pytest
from unittest.mock import patch, MagicMock
import numpy as np
from crml.runtime import run_simulation

def test_run_simulation_valid(valid_crml_file):
    # Mock numpy random to make test deterministic if needed, 
    # but for now we just check it runs without error.
    assert run_simulation(valid_crml_file, n_runs=100) is True

def test_run_simulation_invalid_file(tmp_path):
    p = tmp_path / "invalid.yaml"
    p.write_text("invalid content")
    assert run_simulation(str(p)) is False

def test_run_simulation_unsupported_model(tmp_path):
    content = """
crml: "1.1"
model:
  frequency:
    model: unknown_model
  severity:
    model: lognormal
"""
    p = tmp_path / "unsupported.yaml"
    p.write_text(content)
    assert run_simulation(str(p)) is False
