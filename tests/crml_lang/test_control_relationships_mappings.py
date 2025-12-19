from crml_lang import validate_control_relationships


def test_validate_control_relationships_valid() -> None:
    yaml_text = """
crml_control_relationships: "1.0"
meta:
  name: "scf-to-org-mappings"
relationships:
  id: "scf-overlap-demo"
  relationships:
    - source: "scf:AC-01"
      targets:
        - target: "org:iam-policies"
          relationship_type: "overlaps_with"
          overlap:
            weight: 0.7
            dimensions:
              intent: 0.8
              coverage: 0.6
          groupings:
            - scheme: "nist_csf_function"
              id: "PR"
              label: "Protect"
          description: "Organization IAM policies partially cover the source control objective."
          references:
            - type: "url"
              url: "https://example.com/mapping-notes"
"""

    report = validate_control_relationships(yaml_text, source_kind="yaml")
    assert report.ok, report.render_text(source_label="inline")


def test_validate_control_relationships_rejects_duplicate_edges() -> None:
    yaml_text = """
crml_control_relationships: "1.0"
meta:
  name: "duplicate-edges"
relationships:
  relationships:
    - source: "scf:AC-01"
      targets:
        - target: "org:iam-policies"
          relationship_type: "overlaps_with"
          overlap:
            weight: 0.7
        - target: "org:iam-policies"
          relationship_type: "overlaps_with"
          overlap:
            weight: 0.7
"""

    report = validate_control_relationships(yaml_text, source_kind="yaml")
    assert report.ok is False
    assert any("duplicate" in e.message.lower() for e in report.errors)


def test_validate_control_relationships_rejects_self_edges() -> None:
    yaml_text = """
crml_control_relationships: "1.0"
meta:
  name: "self-edge"
relationships:
  relationships:
    - source: "scf:AC-01"
      targets:
        - target: "scf:AC-01"
          overlap:
            weight: 1.0
"""

    report = validate_control_relationships(yaml_text, source_kind="yaml")
    assert report.ok is False
    assert any("must not be the same" in e.message.lower() for e in report.errors)


def test_validate_control_relationships_allows_backstops_relationship_type() -> None:
    yaml_text = """
crml_control_relationships: "1.0"
meta:
  name: "backstops"
relationships:
  relationships:
    - source: "scf:PR-01"
      targets:
        - target: "org:incident-response"
          relationship_type: "backstops"
          overlap:
            weight: 0.4
"""

    report = validate_control_relationships(yaml_text, source_kind="yaml")
    assert report.ok, report.render_text(source_label="inline")
