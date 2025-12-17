from crml_lang import validate_control_assessment


def test_validate_control_assessment_pack_valid() -> None:
    yaml_text = """
crml_control_assessment: "1.0"
meta:
  name: "acme-cisv8-assessment"
assessment:
  id: "acme-2025-q4"
  framework: "CISv8"
  assessed_at: "2025-12-17T10:15:30Z"
  assessments:
    - id: "cisv8:2.3"
      ref: {standard: "CIS", version: "v8", control: "2", safeguard: "3"}
      implementation_effectiveness: 0.9
      coverage: {value: 0.8, basis: endpoints}
"""

    report = validate_control_assessment(yaml_text, source_kind="yaml")
    assert report.ok, report.render_text(source_label="inline")
