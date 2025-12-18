from __future__ import annotations

from pathlib import Path

from crml_lang import validate
from crml_lang.validators import validate_attack_catalog
from crml_lang.validators import validate_attack_control_relationships


def test_example_attack_catalog_validates() -> None:
    root = Path(__file__).resolve().parents[2]
    example = root / "examples" / "attack_cataloges" / "attck-catalog.yaml"
    report = validate_attack_catalog(str(example), source_kind="path", strict_model=True)
    assert report.ok, report.render_text(source_label=str(example))


def test_example_attck_tagged_scenario_validates() -> None:
    root = Path(__file__).resolve().parents[2]
    example = root / "examples" / "scenarios" / "scenario-attck-metadata.yaml"
    report = validate(str(example), source_kind="path")
    assert report.ok, report.render_text(source_label=str(example))


def test_example_attack_control_relationships_validates() -> None:
    root = Path(__file__).resolve().parents[2]
    example = root / "examples" / "attack_control_relationships" / "attck-to-cisv8-mappings.yaml"
    report = validate_attack_control_relationships(str(example), source_kind="path", strict_model=True)
    assert report.ok, report.render_text(source_label=str(example))
