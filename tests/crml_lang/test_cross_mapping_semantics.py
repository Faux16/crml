from crml_lang import validate_assessment


def test_assessment_can_validate_against_catalog() -> None:
    catalog_yaml = """
crml_control_catalog: "1.0"
meta:
  name: "cisv8-catalog"
catalog:
  framework: "CIS v8"
  controls:
    - id: "cisv8:4.2"
    - id: "cisv8:2.3"
"""

    assessment_yaml = """
crml_assessment: "1.0"
meta:
  name: "acme-assessment"
assessment:
  framework: "CIS v8"
  assessments:
    - id: "cisv8:2.3"
      implementation_effectiveness: 0.9
"""

    report = validate_assessment(
        assessment_yaml,
        source_kind="yaml",
        control_catalogs=[catalog_yaml],
        control_catalogs_source_kind="yaml",
    )
    assert report.ok, report.render_text(source_label="inline")


def test_assessment_rejects_unknown_control_id_when_catalog_provided() -> None:
    catalog_yaml = """
crml_control_catalog: "1.0"
meta:
  name: "cisv8-catalog"
catalog:
  framework: "CIS v8"
  controls:
    - id: "cisv8:4.2"
"""

    assessment_yaml = """
crml_assessment: "1.0"
meta:
  name: "acme-assessment"
assessment:
  framework: "CIS v8"
  assessments:
    - id: "cisv8:2.3"
      implementation_effectiveness: 0.9
"""

    report = validate_assessment(
        assessment_yaml,
        source_kind="yaml",
        control_catalogs=[catalog_yaml],
        control_catalogs_source_kind="yaml",
    )
    assert report.ok is False
    assert any("unknown control id" in e.message.lower() for e in report.errors)


def test_assessment_rejects_duplicate_ids() -> None:
    assessment_yaml = """
crml_assessment: "1.0"
meta:
  name: "acme-assessment"
assessment:
  framework: "CIS v8"
  assessments:
    - id: "cisv8:2.3"
    - id: "cisv8:2.3"
"""

    report = validate_assessment(assessment_yaml, source_kind="yaml")
    assert report.ok is False
    assert any("duplicate" in e.message.lower() for e in report.errors)
