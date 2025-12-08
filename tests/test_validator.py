from crml.validator import validate_crml
import pytest

def test_validate_valid_file(valid_crml_file):
    assert validate_crml(valid_crml_file) is True

def test_validate_invalid_file(tmp_path):
    p = tmp_path / "invalid.yaml"
    p.write_text("not: a valid crml file")
    assert validate_crml(str(p)) is False

def test_validate_missing_file():
    assert validate_crml("non_existent_file.yaml") is False
