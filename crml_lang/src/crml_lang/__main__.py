from __future__ import annotations

import argparse
import sys
from typing import Optional

from .cli import (
    bundle_portfolio_to_yaml,
    import_oscal_catalog_to_control_catalog_yaml,
    import_scf_catalog_to_control_catalog_yaml,
    validate_to_text,
)


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
    b.add_argument("--sort-keys", action="store_true", help="Sort YAML keys")

    o = sub.add_parser(
        "oscal-import-catalog",
        help="Convert an OSCAL Catalog (JSON/YAML) into a CRML skeleton control catalog YAML",
    )
    o.add_argument("in_oscal_catalog", help="Input OSCAL Catalog file path (JSON or YAML)")
    o.add_argument("out_control_catalog", help="Output CRML control catalog YAML file path")
    o.add_argument(
        "--namespace",
        required=True,
        help="CRML namespace to use for generated control ids (e.g. cisv8, nist80053r5)",
    )
    o.add_argument(
        "--framework",
        required=True,
        help="Human framework label to store in the CRML catalog (e.g. 'CIS v8')",
    )
    o.add_argument(
        "--catalog-id",
        default=None,
        help="Optional catalog id (organization-owned). Example: cisv8",
    )
    o.add_argument(
        "--meta-name",
        default=None,
        help="Optional CRML meta.name override for the output document",
    )
    o.add_argument(
        "--source-url",
        default=None,
        help="Optional provenance URL recorded in meta.description",
    )
    o.add_argument(
        "--license-terms",
        default=None,
        help="Optional license/terms note recorded in meta.description",
    )
    o.add_argument("--sort-keys", action="store_true", help="Sort YAML keys")

    s = sub.add_parser(
        "scf-import-catalog",
        help="Convert an SCF Catalog (Excel) into a CRML skeleton control catalog YAML",
    )
    s.add_argument("in_scf_catalog", help="Input SCF Catalog file path (Excel)")
    s.add_argument("out_control_catalog", help="Output CRML control catalog YAML file path")
    s.add_argument("--sort-keys", action="store_true", help="Sort YAML keys")


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

        if args.cmd == "oscal-import-catalog":
            return import_oscal_catalog_to_control_catalog_yaml(
                args.in_oscal_catalog,
                args.out_control_catalog,
                namespace=args.namespace,
                framework=args.framework,
                catalog_id=args.catalog_id,
                meta_name=args.meta_name,
                source_url=args.source_url,
                license_terms=args.license_terms,
                sort_keys=bool(args.sort_keys),
            )

        if args.cmd == "scf-import-catalog":
            return import_scf_catalog_to_control_catalog_yaml(
                args.in_scf_catalog,
                args.out_control_catalog,
                sort_keys=bool(args.sort_keys),
            )


        raise AssertionError(f"Unhandled cmd: {args.cmd}")
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
