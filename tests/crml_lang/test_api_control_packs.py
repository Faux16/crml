from crml_lang import (
    CRControlAssessment,
    CRControlCatalog,
    validate_control_assessment,
    validate_control_catalog,
)


def test_cr_control_catalog_round_trip_yaml() -> None:
    yaml_text = """
crml_control_catalog: "1.0"
meta:
  name: "cisv8-catalog"
catalog:
  framework: "CIS v8"
  controls:
    - id: "cisv8:4.2"
      title: "Secure configuration"
"""

    doc = CRControlCatalog.load_from_yaml_str(yaml_text)
    dumped = doc.dump_to_yaml_str()
    report = validate_control_catalog(dumped, source_kind="yaml")
    assert report.ok, report.render_text(source_label="roundtrip")


def test_cr_control_assessment_round_trip_yaml() -> None:
    yaml_text = """
crml_control_assessment: "1.0"
meta:
  name: "acme-assessment"
assessment:
  framework: "CIS v8"
  assessments:
    - id: "cisv8:2.3"
      implementation_effectiveness: 0.9
      coverage: {value: 0.8, basis: endpoints}
"""

    doc = CRControlAssessment.load_from_yaml_str(yaml_text)
    dumped = doc.dump_to_yaml_str()
    report = validate_control_assessment(dumped, source_kind="yaml")
    assert report.ok, report.render_text(source_label="roundtrip")
