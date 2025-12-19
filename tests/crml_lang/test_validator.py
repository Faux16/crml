from crml_lang import validate
import pytest

def test_validate_valid_file(valid_crml_file):
    report = validate(valid_crml_file, source_kind="path")
    assert report.ok is True

def test_validate_invalid_file(tmp_path):
    p = tmp_path / "invalid.yaml"
    p.write_text("not: a valid crml file")
    report = validate(str(p), source_kind="path")
    assert report.ok is False
    assert report.errors

def test_validate_missing_file():
    report = validate("non_existent_file.yaml", source_kind="path")
    assert report.ok is False
    assert any("File not found" in e.message for e in report.errors)
