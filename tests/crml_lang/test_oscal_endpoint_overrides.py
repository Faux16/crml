from __future__ import annotations

import os

import pytest

from crml_lang.oscal import OscalEndpointNotFoundError, get_endpoint, load_endpoints


def test_get_endpoint_not_found() -> None:
    with pytest.raises(OscalEndpointNotFoundError):
        get_endpoint("does-not-exist")


def test_load_endpoints_allows_external_override(tmp_path, monkeypatch) -> None:
    p = tmp_path / "endpoints.yaml"
    p.write_text(
        """endpoints:\n  - id: bsi-kompendium-grundschutz-plusplus\n    description: Overridden\n    url: https://example.invalid/oscal.json\n    kind: catalog\n    timeout_seconds: 1\n""",
        encoding="utf-8",
    )

    monkeypatch.setenv("CRML_OSCAL_ENDPOINTS_PATH", str(p))
    eps = load_endpoints()
    bsi = next(e for e in eps if e.id == "bsi-kompendium-grundschutz-plusplus")
    assert bsi.description == "Overridden"
    assert bsi.timeout_seconds == pytest.approx(1.0)
