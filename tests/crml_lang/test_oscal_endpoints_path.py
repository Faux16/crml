from __future__ import annotations

import textwrap

from crml_lang.oscal import load_endpoints_from_file


def test_endpoints_support_relative_path(tmp_path) -> None:
    oscal_path = tmp_path / "oscal.json"
    oscal_path.write_text("{}", encoding="utf-8")

    cfg = tmp_path / "endpoints.yaml"
    cfg.write_text(
        textwrap.dedent(
            """
            catalogs:
              - id: local
                description: Local test
                path: ./oscal.json
                catalog_id: local_catalog

            assets: []
            assessments: []
            mappings: []
            """
        ).lstrip(),
        encoding="utf-8",
    )

    eps = load_endpoints_from_file(str(cfg), include_builtin=False, include_env=False)
    assert len(eps) == 1
    e = eps[0]
    assert e.id == "local"
    assert e.url is None
    assert e.path == str(oscal_path.resolve())
    assert e.source == str(oscal_path.resolve())
