import pytest


openpyxl = pytest.importorskip("openpyxl")


from crml_lang import CRControlCatalog, CRAttackCatalog, CRControlRelationships, CRAttackControlRelationships
from crml_lang.mapping import export_xlsx, import_xlsx


def test_xlsx_roundtrip_control_catalog(tmp_path) -> None:
    yaml_text = """
crml_control_catalog: "1.0"
meta:
  name: "demo-catalog"
  tags: ["community"]
catalog:
  framework: "CIS v8"
  controls:
    - id: "cisv8:4.2"
      title: "Secure configuration"
      tags: ["hardening", "baseline"]
      defense_in_depth_layers: ["prevent"]
"""

    doc = CRControlCatalog.load_from_yaml_str(yaml_text)
    out_xlsx = tmp_path / "out.xlsx"

    export_xlsx(str(out_xlsx), control_catalogs=[doc])
    imported = import_xlsx(str(out_xlsx))

    assert len(imported.control_catalogs) == 1
    round_tripped = imported.control_catalogs[0]
    assert round_tripped.model_dump(exclude_none=True) == doc.model_dump(exclude_none=True)


def test_xlsx_roundtrip_attack_catalog(tmp_path) -> None:
    yaml_text = """
crml_attack_catalog: "1.0"
meta:
  name: "demo-attacks"
catalog:
  framework: "MITRE ATT&CK Enterprise"
  attacks:
    - id: "attck:T1059.003"
      title: "Command and Scripting Interpreter: Windows Command Shell"
      tags: ["execution"]
      kill_chain_phases: ["mitre-attack:execution"]
"""

    doc = CRAttackCatalog.load_from_yaml_str(yaml_text)
    out_xlsx = tmp_path / "out.xlsx"

    export_xlsx(str(out_xlsx), attack_catalogs=[doc])
    imported = import_xlsx(str(out_xlsx))

    assert len(imported.attack_catalogs) == 1
    round_tripped = imported.attack_catalogs[0]
    assert round_tripped.model_dump(exclude_none=True) == doc.model_dump(exclude_none=True)


def test_xlsx_roundtrip_control_relationships(tmp_path) -> None:
    yaml_text = """
crml_control_relationships: "1.0"
meta:
  name: "demo-relationships"
relationships:
  relationships:
    - source: "cisv8:4.2"
      targets:
        - target: "cap:secure-config"
          relationship_type: "mitigates"
          overlap:
            weight: 0.8
            dimensions:
              coverage: 0.9
            rationale: "Same mitigation objective"
          confidence: 0.7
          groupings:
            - scheme: "nist_csf_function"
              id: "PR"
              label: "Protect"
          references:
            - type: "url"
              url: "https://example.com"
"""

    doc = CRControlRelationships.load_from_yaml_str(yaml_text)
    out_xlsx = tmp_path / "out.xlsx"

    export_xlsx(str(out_xlsx), control_relationships=[doc])
    imported = import_xlsx(str(out_xlsx))

    assert len(imported.control_relationships) == 1
    round_tripped = imported.control_relationships[0]
    assert round_tripped.model_dump(exclude_none=True) == doc.model_dump(exclude_none=True)


def test_xlsx_roundtrip_attack_control_relationships(tmp_path) -> None:
    yaml_text = """
crml_attack_control_relationships: "1.0"
meta:
  name: "demo-attck-mappings"
relationships:
  metadata:
    source: "internal"
  relationships:
    - attack: "attck:T1059.003"
      targets:
        - control: "cap:edr"
          relationship_type: "detectable_by"
          strength: 0.6
          confidence: 0.8
          tags: ["endpoint"]
          references:
            - type: "document"
              label: "IR playbook"
"""

    doc = CRAttackControlRelationships.load_from_yaml_str(yaml_text)
    out_xlsx = tmp_path / "out.xlsx"

    export_xlsx(str(out_xlsx), attack_control_relationships=[doc])
    imported = import_xlsx(str(out_xlsx))

    assert len(imported.attack_control_relationships) == 1
    round_tripped = imported.attack_control_relationships[0]
    assert round_tripped.model_dump(exclude_none=True) == doc.model_dump(exclude_none=True)


def test_xlsx_export_accepts_paths(tmp_path) -> None:
    catalog_yaml = """
crml_control_catalog: "1.0"
meta:
  name: "demo-catalog"
catalog:
  framework: "CIS v8"
  controls:
    - id: "cisv8:4.2"
      title: "Secure configuration"
"""
    rels_yaml = """
crml_control_relationships: "1.0"
meta:
  name: "demo-relationships"
relationships:
  relationships:
    - source: "cisv8:4.2"
      targets:
        - target: "cap:secure-config"
          overlap:
            weight: 0.5
"""
    attacks_yaml = """
crml_attack_catalog: "1.0"
meta:
  name: "demo-attacks"
catalog:
  framework: "MITRE ATT&CK Enterprise"
  attacks:
    - id: "attck:T1059.003"
"""
    attck_rels_yaml = """
crml_attack_control_relationships: "1.0"
meta:
  name: "demo-attck-mappings"
relationships:
  relationships:
    - attack: "attck:T1059.003"
      targets:
        - control: "cap:edr"
          relationship_type: "detectable_by"
"""

    cat_path = tmp_path / "catalog.yaml"
    rels_path = tmp_path / "rels.yaml"
    attacks_path = tmp_path / "attacks.yaml"
    attck_rels_path = tmp_path / "attck_rels.yaml"

    cat_path.write_text(catalog_yaml, encoding="utf-8")
    rels_path.write_text(rels_yaml, encoding="utf-8")
    attacks_path.write_text(attacks_yaml, encoding="utf-8")
    attck_rels_path.write_text(attck_rels_yaml, encoding="utf-8")

    out_xlsx = tmp_path / "out.xlsx"
    export_xlsx(
        str(out_xlsx),
        control_catalog_paths=[cat_path],
        attack_catalog_paths=[attacks_path],
        control_relationship_paths=[rels_path],
        attack_control_relationship_paths=[attck_rels_path],
    )

    imported = import_xlsx(str(out_xlsx))
    assert len(imported.control_catalogs) == 1
    assert len(imported.attack_catalogs) == 1
    assert len(imported.control_relationships) == 1
    assert len(imported.attack_control_relationships) == 1
