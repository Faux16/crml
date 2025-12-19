from crml_lang import validate_assessment


def test_validate_assessment_catalog_valid() -> None:
    yaml_text = """
crml_assessment: "1.0"
meta:
  name: "acme-cisv8-assessment"
assessment:
  id: "acme-2025-q4"
  framework: "CISv8"
  assessed_at: "2025-12-17T10:15:30Z"
  assessments:
    - id: "cisv8:2.3"
      ref: {standard: "CIS", version: "v8", control: "2", safeguard: "3"}
      scf_cmm_level: 4
"""

    report = validate_assessment(yaml_text, source_kind="yaml")
    assert report.ok, report.render_text(source_label="inline")


def test_validate_assessment_catalog_accepts_quantitative_posture_fields() -> None:
    yaml_text = """
crml_assessment: "1.0"
meta:
  name: "acme-cisv8-assessment"
assessment:
  framework: "CISv8"
  assessments:
    - id: "cisv8:2.3"
      implementation_effectiveness: 0.9
      coverage: {value: 0.8, basis: endpoints}
      reliability: 0.95
"""

    report = validate_assessment(yaml_text, source_kind="yaml")
    assert report.ok, report.render_text(source_label="inline")


def test_validate_assessment_catalog_rejects_mixed_quantitative_and_cmm() -> None:
    yaml_text = """
crml_assessment: "1.0"
meta:
  name: "acme-assessment"
assessment:
  framework: "Org"
  assessments:
    - id: "org:iam.mfa"
      scf_cmm_level: 3
      implementation_effectiveness: 0.7
"""

    report = validate_assessment(yaml_text, source_kind="yaml", strict_model=True)
    assert report.ok is False
    assert any("either scf_cmm_level" in e.message for e in report.errors)


def test_validate_assessment_catalog_rejects_entry_with_no_answers() -> None:
    yaml_text = """
crml_assessment: "1.0"
meta:
  name: "acme-assessment"
assessment:
  framework: "Org"
  assessments:
    - id: "org:iam.mfa"
"""

    report = validate_assessment(yaml_text, source_kind="yaml", strict_model=True)
    assert report.ok is False
    assert any("must provide either" in e.message.lower() for e in report.errors)
