from __future__ import annotations

import json
import textwrap

from crml_lang import CRAssessment, CRControlCatalog


def test_oscal_endpoint_locale_validation_forbids_country_without_region(tmp_path) -> None:
    from crml_lang.oscal import load_endpoints_from_file

    cfg = tmp_path / "endpoints.yaml"
    cfg.write_text(
        textwrap.dedent(
            """\
            catalogs:
              - id: ex
                description: Example
                path: ./catalog.json
                catalog_id: example
                meta:
                  locale:
                    countries: [DE]
            assessments: []
            assets: []
            mappings: []
            """
        ),
        encoding="utf-8",
    )

    (tmp_path / "catalog.json").write_text(
        json.dumps({"catalog": {"metadata": {"title": "Example"}, "controls": [{"id": "AC-1"}]}}),
        encoding="utf-8",
    )

    try:
        load_endpoints_from_file(str(cfg), include_builtin=False, include_env=False)
        raise AssertionError("Expected ValueError")
    except ValueError as e:
        assert "must not set countries" in str(e)


def test_control_catalog_from_endpoint_allows_region_only_locale(tmp_path) -> None:
    from crml_lang.oscal import load_endpoints_from_file
    from crml_lang.oscal.helpers import control_catalog_from_endpoint_obj

    (tmp_path / "catalog.json").write_text(
        json.dumps({"catalog": {"metadata": {"title": "Example Catalog"}, "controls": [{"id": "AC-1"}]}}),
        encoding="utf-8",
    )

    cfg = tmp_path / "endpoints.yaml"
    cfg.write_text(
        textwrap.dedent(
            """\
            catalogs:
              - id: ex
                description: Example
                path: ./catalog.json
                catalog_id: example
                regions: [europe]
            assessments: []
            assets: []
            mappings: []
            """
        ),
        encoding="utf-8",
    )

    endpoints = load_endpoints_from_file(str(cfg), include_builtin=False, include_env=False)
    endpoint = endpoints[0]
    assert endpoint.locale is not None
    assert endpoint.locale.regions == ["europe"]
    assert endpoint.locale.countries == []

    catalog, _prov = control_catalog_from_endpoint_obj(endpoint)
    assert catalog.meta.locale.get("regions") == ["europe"]
    assert catalog.meta.locale.get("countries") == []


def test_control_catalog_from_endpoint_injects_locale(tmp_path) -> None:
    from crml_lang.oscal import load_endpoints_from_file
    from crml_lang.oscal.helpers import control_catalog_from_endpoint_obj

    (tmp_path / "catalog.json").write_text(
        json.dumps(
            {
                "catalog": {
                    "metadata": {"title": "Example Catalog"},
                    "controls": [
                        {
                            "id": "AC-1",
                            "title": "Access Control Policy",
                            "uuid": "11111111-1111-1111-1111-111111111111",
                        }
                    ],
                }
            }
        ),
        encoding="utf-8",
    )

    cfg = tmp_path / "endpoints.yaml"
    cfg.write_text(
        textwrap.dedent(
            """\
            catalogs:
              - id: ex
                description: Example
                path: ./catalog.json
                catalog_id: example
                regions: [europe]
                countries: [DE]
            assessments: []
            assets: []
            mappings: []
            """
        ),
        encoding="utf-8",
    )

    endpoints = load_endpoints_from_file(str(cfg), include_builtin=False, include_env=False)
    assert len(endpoints) == 1
    endpoint = endpoints[0]
    assert endpoint.locale is not None
    assert endpoint.locale.regions == ["europe"]
    assert endpoint.locale.countries == ["DE"]

    catalog, _prov = control_catalog_from_endpoint_obj(endpoint)
    assert catalog.meta.locale.get("regions") == ["europe"]
    assert catalog.meta.locale.get("countries") == ["DE"]


def test_control_catalog_from_endpoint_injects_industries(tmp_path) -> None:
    from crml_lang.oscal import load_endpoints_from_file
    from crml_lang.oscal.helpers import control_catalog_from_endpoint_obj

    (tmp_path / "catalog.json").write_text(
        json.dumps({"catalog": {"metadata": {"title": "Example Catalog"}, "controls": [{"id": "AC-1"}]}}),
        encoding="utf-8",
    )

    cfg = tmp_path / "endpoints.yaml"
    cfg.write_text(
        textwrap.dedent(
            """\
            catalogs:
              - id: ex
                description: Example
                path: ./catalog.json
                catalog_id: example
                industries: ["financial-services", "healthcare"]
            assessments: []
            assets: []
            mappings: []
            """
        ),
        encoding="utf-8",
    )

    endpoints = load_endpoints_from_file(str(cfg), include_builtin=False, include_env=False)
    endpoint = endpoints[0]
    assert endpoint.industries == ["financial-services", "healthcare"]

    catalog, _prov = control_catalog_from_endpoint_obj(endpoint)
    assert catalog.meta.industries == ["financial-services", "healthcare"]


def test_control_catalog_from_endpoint_uses_crml_meta_object(tmp_path) -> None:
    from crml_lang.oscal import load_endpoints_from_file
    from crml_lang.oscal.helpers import control_catalog_from_endpoint_obj

    (tmp_path / "catalog.json").write_text(
        json.dumps({"catalog": {"metadata": {"title": "Example Catalog"}, "controls": [{"id": "AC-1"}]}}),
        encoding="utf-8",
    )

    cfg = tmp_path / "endpoints.yaml"
    cfg.write_text(
        textwrap.dedent(
            """\
            catalogs:
              - id: ex
                description: Example
                path: ./catalog.json
                catalog_id: example
                meta:
                  industries: ["financial-services"]
                  locale:
                    regions: [europe]
                    countries: [DE]
                    note: keep-this
            assessments: []
            assets: []
            mappings: []
            """
        ),
        encoding="utf-8",
    )

    endpoints = load_endpoints_from_file(str(cfg), include_builtin=False, include_env=False)
    endpoint = endpoints[0]
    assert endpoint.meta_overrides is not None
    assert endpoint.meta_overrides["industries"] == ["financial-services"]
    assert endpoint.meta_overrides["locale"]["note"] == "keep-this"

    # Extra locale keys are preserved.
    catalog, _prov = control_catalog_from_endpoint_obj(endpoint)
    assert catalog.meta.industries == ["financial-services"]
    assert catalog.meta.locale.get("regions") == ["europe"]
    assert catalog.meta.locale.get("countries") == ["DE"]
    assert catalog.meta.locale.get("note") == "keep-this"


def test_control_catalog_from_oscal_minimal_catalog_dict(tmp_path) -> None:
    oscal = {
        "catalog": {
            "metadata": {"title": "Example Catalog"},
            "groups": [
                {
                    "id": "grp1",
                    "title": "Group 1",
                    "controls": [
                        {"id": "AC-1", "title": "Access Control Policy", "uuid": "11111111-1111-1111-1111-111111111111"},
                        {"id": "AC-2", "title": "Account Management"},
                    ],
                }
            ],
        }
    }

    p = tmp_path / "catalog.json"
    p.write_text(json.dumps(oscal), encoding="utf-8")

    catalog = CRControlCatalog.fromOscal(str(p), catalog_id="example")

    assert catalog.crml_control_catalog == "1.0"
    assert catalog.catalog.framework == "Example Catalog"
    assert len(catalog.catalog.controls) == 2
    assert {c.id for c in catalog.catalog.controls} == {
        "example-catalog:AC-1",
        "example-catalog:AC-2",
    }

    assert catalog.catalog.groups is not None
    assert len(catalog.catalog.groups) == 1
    g = catalog.catalog.groups[0]
    assert g.id == "grp1"
    assert g.title == "Group 1"
    assert set(g.control_ids or []) == {"example-catalog:AC-1", "example-catalog:AC-2"}


def test_control_catalog_from_oscal_is_deterministically_sorted_and_yaml_headers_stay_on_top(tmp_path) -> None:
    # Intentionally reversed OSCAL control order.
    oscal = {
        "catalog": {
            "metadata": {"title": "Example Catalog"},
            "controls": [
                {"id": "AC-2", "title": "Account Management"},
                {"id": "AC-1", "title": "Access Control Policy"},
            ],
        }
    }

    p = tmp_path / "catalog.json"
    p.write_text(json.dumps(oscal), encoding="utf-8")

    catalog = CRControlCatalog.fromOscal(str(p), catalog_id="example")

    # Controls are sorted by canonical CRML id for stable diffs.
    assert [c.id for c in catalog.catalog.controls] == [
        "example-catalog:AC-1",
        "example-catalog:AC-2",
    ]

    # Even with sort_keys=True, the CRML header keys should remain at the top.
    yaml_text = catalog.dump_to_yaml_str(sort_keys=True)
    lines = [ln for ln in yaml_text.splitlines() if ln.strip()]
    assert lines[0].startswith("crml_control_catalog:")
    assert lines[1].startswith("meta:")
    assert yaml_text.find("\ncrml_control_catalog:") < yaml_text.find("\nmeta:") < yaml_text.find("\ncatalog:")


def test_oscal_group_uuid_and_prose_map_to_crml_group_fields() -> None:
    from crml_lang.oscal.convert import oscal_catalog_to_crml_control_catalog

    oscal = {
        "catalog": {
            "metadata": {"title": "Example Catalog"},
            "groups": [
                {
                    "id": "grp1",
                    "uuid": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                    "title": "Group 1",
                    "prose": "Top-level group prose.",
                    "parts": [
                        {"name": "guidance", "prose": "Additional group guidance."},
                    ],
                    "controls": [{"id": "AC-1"}],
                }
            ],
        }
    }

    payload = oscal_catalog_to_crml_control_catalog(
        oscal,
        namespace="example",
        framework="Example Catalog",
        include_prose=True,
    )

    groups = (payload.get("catalog") or {}).get("groups") or []
    assert len(groups) == 1
    g = groups[0]
    assert g.get("id") == "grp1"
    assert g.get("oscal_uuid") == "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    assert "Top-level group prose." in (g.get("description") or "")
    assert "Additional group guidance." in (g.get("description") or "")


def test_assessment_from_oscal_generates_template(tmp_path) -> None:
    oscal = {
        "catalog": {
            "metadata": {"title": "BSI Example"},
            "controls": [
                {"id": "C-1", "uuid": "22222222-2222-2222-2222-222222222222"},
                {"id": "C-2"},
            ]
        }
    }

    p = tmp_path / "catalog.json"
    p.write_text(json.dumps(oscal), encoding="utf-8")

    assessment = CRAssessment.fromOscal(
        str(p),
        assessment_id="bsi-example",
        default_scf_cmm_level=0,
    )

    assert assessment.crml_assessment == "1.0"
    assert assessment.assessment.framework == "BSI Example"
    assert len(assessment.assessment.assessments) == 2
    assert {a.id for a in assessment.assessment.assessments} == {
        "bsi-example:C-1",
        "bsi-example:C-2",
    }
    assert all(a.scf_cmm_level == 0 for a in assessment.assessment.assessments)


def test_oscal_metadata_remarks_maps_to_crml_meta_description_and_reference_is_url_only() -> None:
    from crml_lang.oscal.convert import oscal_catalog_to_crml_control_catalog

    oscal = {
        "catalog": {
            "metadata": {
                "title": "Example Catalog",
                "remarks": "These are OSCAL remarks.",
            },
            "controls": [{"id": "AC-1"}],
        }
    }

    payload_url = oscal_catalog_to_crml_control_catalog(
        oscal,
        namespace="example",
        framework="Example Catalog",
        source_url="https://example.invalid/oscal.json",
    )
    assert "These are OSCAL remarks." in (payload_url.get("meta") or {}).get("description", "")
    assert (payload_url.get("meta") or {}).get("reference") == "https://example.invalid/oscal.json"

    payload_path = oscal_catalog_to_crml_control_catalog(
        oscal,
        namespace="example",
        framework="Example Catalog",
        source_url=r"C:\\local\\catalog.json",
    )
    assert "These are OSCAL remarks." in (payload_path.get("meta") or {}).get("description", "")
    assert (payload_path.get("meta") or {}).get("reference") is None


def test_oscal_control_prose_maps_to_crml_control_description() -> None:
    from crml_lang.oscal.convert import oscal_catalog_to_crml_control_catalog

    oscal = {
        "catalog": {
            "metadata": {"title": "Example Catalog"},
            "controls": [
                {
                    "id": "AC-1",
                    "title": "Access Control Policy",
                    "parts": [
                        {"name": "statement", "prose": "Ensure an access control policy is established."},
                        {
                            "name": "guidance",
                            "parts": [
                                {"name": "item", "prose": "Document scope and review cadence."}
                            ],
                        },
                    ],
                }
            ],
        }
    }

    payload = oscal_catalog_to_crml_control_catalog(
        oscal,
        namespace="example",
        framework="Example Catalog",
    )

    controls = (payload.get("catalog") or {}).get("controls") or []
    assert len(controls) == 1
    assert controls[0]["id"] == "example:AC-1"
    assert "Ensure an access control policy" in controls[0].get("description", "")
    assert "Document scope and review cadence" in controls[0].get("description", "")


def test_scf_standard_mapping_uses_statement_and_objectives_only() -> None:
    from crml_lang.oscal.convert import oscal_catalog_to_crml_control_catalog
    from crml_lang.oscal.standards import get_control_text_options

    oscal = {
        "catalog": {
            "metadata": {"title": "SCF 2025.3"},
            "controls": [
                {
                    "id": "GOV-01",
                    "title": "Cybersecurity Governance",
                    "parts": [
                        {"name": "statement", "prose": "Mechanisms exist to do the thing."},
                        {
                            "name": "maturity",
                            "id": "CMM-1",
                            "class": "C|P-CMM",
                            "prose": "Very long maturity rubric text that should not be in the catalog description.",
                        },
                        {"name": "objective", "id": "GOV-01_A01", "prose": "an organization-wide program is developed."},
                        {"name": "objective", "id": "GOV-01_A02", "prose": "management commitment is addressed."},
                    ],
                }
            ],
        }
    }

    opts = get_control_text_options("scf")
    assert opts is not None

    payload = oscal_catalog_to_crml_control_catalog(
        oscal,
        namespace="scf2025",
        framework="SCF 2025.3",
        control_text_options=opts,
    )

    controls = (payload.get("catalog") or {}).get("controls") or []
    assert len(controls) == 1
    desc = controls[0].get("description") or ""

    assert "Mechanisms exist" in desc
    assert "Objectives:" in desc
    assert "GOV-01_A01" in desc
    assert "organization-wide program" in desc
    assert "maturity rubric" not in desc


def test_oscal_standard_detection_uses_prefix_matching() -> None:
    from crml_lang.oscal.standards import detect_standard_id

    assert detect_standard_id(endpoint_id="scf2025") == "scf"
    assert detect_standard_id(endpoint_id="SCF-foo") == "scf"
    assert detect_standard_id(endpoint_id="bsi_gspp_2023") is None


def test_oscal_catalog_uuid_and_control_alt_identifier_map_to_crml_oscal_uuid() -> None:
    from crml_lang.oscal.convert import oscal_catalog_to_crml_control_catalog

    oscal = {
        "catalog": {
            "uuid": "754c1ce8-3bba-4adf-b696-02aed030b524",
            "metadata": {"title": "Example Catalog"},
            "controls": [
                {
                    "id": "GC.1.1",
                    "title": "Example",
                    "props": [
                        {"name": "alt-identifier", "value": "80351189-6ffc-495e-a995-6219b9704724"}
                    ],
                }
            ],
        }
    }

    payload = oscal_catalog_to_crml_control_catalog(
        oscal,
        namespace="bsi_gspp_2023",
        framework="Example Catalog",
        catalog_id="bsi_gspp_2023",
    )

    assert ((payload.get("catalog") or {}).get("oscal_uuid")) == "754c1ce8-3bba-4adf-b696-02aed030b524"
    controls = (payload.get("catalog") or {}).get("controls") or []
    assert len(controls) == 1
    assert controls[0].get("oscal_uuid") == "80351189-6ffc-495e-a995-6219b9704724"
