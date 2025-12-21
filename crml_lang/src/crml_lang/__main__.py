from __future__ import annotations

import argparse
import sys
from typing import Optional

from .cli import (
    bundle_portfolio_to_yaml,
    oscal_generate_catalogs,
    oscal_import_assessment_template,
    oscal_import_catalog,
    oscal_list_endpoints,
    validate_to_text,
)

_SORT_KEYS_HELP = "Sort YAML keys"


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="crml-lang", description="crml-lang CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate", help="Validate a CRML YAML document")
    v.add_argument("file", help="Path to CRML YAML file")

    b = sub.add_parser(
        "bundle-portfolio",
        help="Bundle a CRML portfolio into a single portfolio bundle YAML artifact",
    )
    b.add_argument("in_portfolio", help="Path to CRML portfolio YAML file")
    b.add_argument("out_bundle", help="Output portfolio bundle YAML file path")
    b.add_argument("--sort-keys", action="store_true", help=_SORT_KEYS_HELP)

    o = sub.add_parser("oscal", help="OSCAL helpers (endpoints + conversions)")
    osub = o.add_subparsers(dest="oscal_cmd", required=True)

    le = osub.add_parser("list-endpoints", help="List configured OSCAL endpoints")
    le.add_argument(
        "--format",
        default="text",
        choices=["text", "json"],
        help="Output format",
    )

    ic = osub.add_parser("import-catalog", help="Convert OSCAL catalog into CRML control catalog YAML")
    src = ic.add_mutually_exclusive_group(required=True)
    src.add_argument("--endpoint", default=None, help="Endpoint id (see: crml-lang oscal list-endpoints)")
    src.add_argument("--path", default=None, help="Local OSCAL file path (JSON or YAML)")
    ic.add_argument("--out", required=True, help="Output CRML YAML path")
    ic.add_argument("--sort-keys", action="store_true", help=_SORT_KEYS_HELP)

    ia = osub.add_parser(
        "import-assessment-template",
        help="Convert OSCAL catalog into CRML assessment template YAML",
    )
    src2 = ia.add_mutually_exclusive_group(required=True)
    src2.add_argument("--endpoint", default=None, help="Endpoint id (see: crml-lang oscal list-endpoints)")
    src2.add_argument("--path", default=None, help="Local OSCAL file path (JSON or YAML)")
    ia.add_argument("--out", required=True, help="Output CRML YAML path")
    ia.add_argument("--sort-keys", action="store_true", help=_SORT_KEYS_HELP)

    gc = osub.add_parser(
        "export-catalogs",
        help="Export CRML control catalogs for all catalog endpoints in a config file",
    )
    gc.add_argument("--config", required=True, help="Endpoints config YAML (catalogs/assets/assessments/mappings)")
    gc.add_argument("--out-dir", required=True, help="Output directory for generated CRML YAML files")
    gc.add_argument("--sort-keys", action="store_true", help=_SORT_KEYS_HELP)

    # Backwards-compatible alias.
    gc_old = osub.add_parser(
        "generate-catalogs",
        help="(deprecated) Alias for: export-catalogs",
    )
    gc_old.add_argument(
        "--config", required=True, help="Endpoints config YAML (catalogs/assets/assessments/mappings)"
    )
    gc_old.add_argument("--out-dir", required=True, help="Output directory for generated CRML YAML files")
    gc_old.add_argument("--sort-keys", action="store_true", help=_SORT_KEYS_HELP)

    return p


def main(argv: Optional[list[str]] = None) -> int:
    try:
        args = _build_parser().parse_args(argv)

        if args.cmd == "validate":
            return validate_to_text(args.file)

        if args.cmd == "bundle-portfolio":
            return bundle_portfolio_to_yaml(
                args.in_portfolio,
                args.out_bundle,
                sort_keys=bool(args.sort_keys),
            )

        if args.cmd == "oscal":
            if args.oscal_cmd == "list-endpoints":
                return oscal_list_endpoints(fmt=str(args.format))
            if args.oscal_cmd == "import-catalog":
                return oscal_import_catalog(
                    out=str(args.out),
                    endpoint=args.endpoint,
                    path=args.path,
                    sort_keys=bool(args.sort_keys),
                )
            if args.oscal_cmd == "import-assessment-template":
                return oscal_import_assessment_template(
                    out=str(args.out),
                    endpoint=args.endpoint,
                    path=args.path,
                    sort_keys=bool(args.sort_keys),
                )
            if args.oscal_cmd in {"export-catalogs", "generate-catalogs"}:
                return oscal_generate_catalogs(
                    config=str(args.config),
                    out_dir=str(args.out_dir),
                    sort_keys=bool(args.sort_keys),
                )
            raise AssertionError(f"Unhandled oscal_cmd: {args.oscal_cmd}")

        raise AssertionError(f"Unhandled cmd: {args.cmd}")
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
