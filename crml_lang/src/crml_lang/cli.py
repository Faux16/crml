"""Command-line helpers for crml-lang.

This module is intentionally small and stable. Engine CLIs can delegate to these
helpers so the core language behaviors (e.g. bundling) live in `crml_lang`.

Note: `crml_lang` also has a separate XLSX-focused CLI under
`crml_lang.mapping.__main__`.
"""

from __future__ import annotations

from typing import Optional, TextIO

import json
import sys


def bundle_portfolio_to_yaml(
    in_portfolio: str,
    out_bundle: str,
    *,
    sort_keys: bool = False,
    stdout: Optional[TextIO] = None,
    stderr: Optional[TextIO] = None,
) -> int:
    """Bundle a portfolio from `in_portfolio` and write a bundle YAML to `out_bundle`.

    Returns a process-style exit code (0 on success, 1 on failure).
    """

    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr

    from crml_lang import CRPortfolioBundle, bundle_portfolio

    report = bundle_portfolio(in_portfolio, source_kind="path")
    if not report.ok or report.bundle is None:
        for m in report.errors:
            print(m.message, file=stderr)
        return 1

    bundle = CRPortfolioBundle.model_validate(
        report.bundle.model_dump(by_alias=True, exclude_none=True)
    )
    bundle.dump_to_yaml(out_bundle, sort_keys=bool(sort_keys))
    print(f"Wrote {out_bundle}", file=stdout)
    return 0


def validate_to_text(
    path: str,
    *,
    stdout: Optional[TextIO] = None,
    stderr: Optional[TextIO] = None,
) -> int:
    """Validate a CRML YAML document at `path` and print a rendered report.

    Returns a process-style exit code (0 if valid, 1 otherwise).
    """

    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr

    try:
        from crml_lang import validate_document

        report = validate_document(path, source_kind="path")
        print(report.render_text(source_label=path), file=stdout)
        return 0 if report.ok else 1
    except Exception as e:
        print(str(e), file=stderr)
        return 1


def oscal_list_endpoints(
    *,
    fmt: str = "text",
    stdout: Optional[TextIO] = None,
    stderr: Optional[TextIO] = None,
) -> int:
    """List configured OSCAL endpoints.

    `fmt` can be: text|json.
    """

    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr

    try:
        from crml_lang.oscal import list_endpoints

        items = list_endpoints()
        if fmt == "json":
            print(json.dumps({"endpoints": items}, indent=2, sort_keys=True), file=stdout)
            return 0

        # text
        for e in sorted(items, key=lambda x: str(x.get("id", ""))):
            print(f"{e.get('id')}\t{e.get('kind')}\t{e.get('description')}\t{e.get('url')}", file=stdout)
        return 0
    except Exception as e:
        print(str(e), file=stderr)
        return 1


def oscal_import_catalog(
    *,
    out: str,
    endpoint: Optional[str] = None,
    path: Optional[str] = None,
    sort_keys: bool = False,
    stdout: Optional[TextIO] = None,
    stderr: Optional[TextIO] = None,
) -> int:
    """Import an OSCAL catalog into a CRML control catalog YAML."""

    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr

    try:
        from crml_lang import CRControlCatalog
        from crml_lang.oscal import control_catalog_from_endpoint

        if (endpoint is None) == (path is None):
            raise ValueError("Provide exactly one of: endpoint, path")

        if endpoint is not None:
            catalog, prov = control_catalog_from_endpoint(endpoint)
            catalog.dump_to_yaml(out, sort_keys=bool(sort_keys))
            print(f"Wrote CRML YAML {out}", file=stdout)
            print(f"Source: {prov.source}", file=stdout)
            return 0

        assert path is not None
        catalog = CRControlCatalog.fromOscal(path)
        catalog.dump_to_yaml(out, sort_keys=bool(sort_keys))
        print(f"Wrote CRML YAML {out}", file=stdout)
        print(f"Source: {path}", file=stdout)
        return 0
    except Exception as e:
        print(str(e), file=stderr)
        return 1


def oscal_import_assessment_template(
    *,
    out: str,
    endpoint: Optional[str] = None,
    path: Optional[str] = None,
    sort_keys: bool = False,
    stdout: Optional[TextIO] = None,
    stderr: Optional[TextIO] = None,
) -> int:
    """Import an OSCAL catalog into a CRML assessment template YAML."""

    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr

    try:
        from crml_lang import CRAssessment
        from crml_lang.oscal import assessment_template_from_endpoint

        if (endpoint is None) == (path is None):
            raise ValueError("Provide exactly one of: endpoint, path")

        if endpoint is not None:
            assessment, prov = assessment_template_from_endpoint(endpoint)
            assessment.dump_to_yaml(out, sort_keys=bool(sort_keys))
            print(f"Wrote CRML YAML {out}", file=stdout)
            print(f"Source: {prov.source}", file=stdout)
            return 0

        assert path is not None
        assessment = CRAssessment.fromOscal(path)
        assessment.dump_to_yaml(out, sort_keys=bool(sort_keys))
        print(f"Wrote CRML YAML {out}", file=stdout)
        print(f"Source: {path}", file=stdout)
        return 0
    except Exception as e:
        print(str(e), file=stderr)
        return 1
