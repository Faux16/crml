from __future__ import annotations

from crml_lang.oscal import load_endpoints


def test_load_endpoints_includes_bsi_grundschutz() -> None:
    eps = load_endpoints()
    ids = {e.catalog_id for e in eps}
    assert "bsi_gspp_2023" in ids

    bsi = next(e for e in eps if e.catalog_id == "bsi_gspp_2023")
    assert bsi.kind == "catalog"
    assert "BSI Kompendium Grundschutz++" in bsi.description
    assert bsi.url.startswith("https://")
    assert bsi.timeout_seconds > 0
