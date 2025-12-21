from __future__ import annotations

import json

from crml_lang import CRAssessment, CRControlCatalog


def test_control_catalog_from_oscal_minimal_catalog_dict(tmp_path) -> None:
    oscal = {
        "catalog": {
            "metadata": {"title": "Example Catalog"},
            "groups": [
                {
                    "id": "grp1",
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
