"""Command-line helpers for crml-lang.

This module is intentionally small and stable. Engine CLIs can delegate to these
helpers so the core language behaviors (e.g. bundling) live in `crml_lang`.

Note: `crml_lang` also has a separate XLSX-focused CLI under
`crml_lang.mapping.__main__`.
"""

from __future__ import annotations

from typing import Optional, TextIO

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


def import_oscal_catalog_to_control_catalog_yaml(
    in_oscal_catalog: str,
    out_control_catalog: str,
    *,
    namespace: str,
    framework: str,
    catalog_id: Optional[str] = None,
    meta_name: Optional[str] = None,
    source_url: Optional[str] = None,
    license_terms: Optional[str] = None,
    sort_keys: bool = False,
    stdout: Optional[TextIO] = None,
    stderr: Optional[TextIO] = None,
) -> int:
    """Convert an OSCAL catalog to a CRML skeleton control catalog YAML.

    This requires optional dependencies: `pip install "crml-lang[oscal]"`.
    """

    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr

    try:
        from crml_lang.integrations.oscal import (
            OscalCatalogProvenance,
            oscal_catalog_to_crml_control_catalog,
            read_oscal_catalog,
        )

        oscal_catalog = read_oscal_catalog(in_oscal_catalog)
        crml_catalog = oscal_catalog_to_crml_control_catalog(
            oscal_catalog,
            namespace=namespace,
            framework=framework,
            catalog_id=catalog_id,
            meta_name=meta_name,
            provenance=OscalCatalogProvenance(
                source_path=in_oscal_catalog,
                source_url=source_url,
                license=license_terms,
            ),
        )

        crml_catalog.dump_to_yaml(out_control_catalog, sort_keys=bool(sort_keys))
        print(f"Wrote {out_control_catalog}", file=stdout)
        return 0
    except ImportError as e:
        print(str(e), file=stderr)
        return 2
    except Exception as e:
        print(str(e), file=stderr)
        return 1
