from __future__ import annotations

from pathlib import Path

from crml_lang import validate_attack_control_relationships


def test_validate_attack_control_relationships_valid() -> None:
    yaml_text = """
crml_attack_control_relationships: "1.0"
meta:
  name: "Example"
relationships:
  id: "mapping"
  relationships:
    - attack: "attck:T1059.003"
      targets:
        - control: "cisv8:8.2"
          relationship_type: mitigated_by
"""
    report = validate_attack_control_relationships(yaml_text, source_kind="yaml", strict_model=True)
    assert report.ok, report.render_text(source_label="(yaml)")


def test_validate_attack_control_relationships_rejects_duplicate_attacks() -> None:
    yaml_text = """
crml_attack_control_relationships: "1.0"
meta:
  name: "Example"
relationships:
  relationships:
    - attack: "attck:T1059.003"
      targets:
        - control: "cisv8:8.2"
          relationship_type: mitigated_by
    - attack: "attck:T1059.003"
      targets:
        - control: "cisv8:8.5"
          relationship_type: detectable_by
"""
    report = validate_attack_control_relationships(yaml_text, source_kind="yaml")
    assert not report.ok


def test_example_attack_control_relationships_validates() -> None:
    root = Path(__file__).resolve().parents[2]
    example = root / "examples" / "attack_control_relationships" / "attck-to-cisv8-mappings.yaml"
    report = validate_attack_control_relationships(str(example), source_kind="path", strict_model=True)
    assert report.ok, report.render_text(source_label=str(example))
