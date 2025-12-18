from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..api import CRControlCatalog, CRAttackCatalog, CRControlRelationships, CRAttackControlRelationships
from .xlsx import export_xlsx, import_xlsx, write_imported_as_yaml


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m crml_lang.mapping")
    sub = p.add_subparsers(dest="cmd", required=True)

    exp = sub.add_parser("export-xlsx", help="Export CRML YAML documents to an XLSX workbook")
    exp.add_argument("--out", required=True, help="Output XLSX file path")
    exp.add_argument(
        "--control-catalog",
        action="append",
        default=[],
        help="Path to a CRML control catalog YAML file (repeatable)",
    )
    exp.add_argument(
        "--attack-catalog",
        action="append",
        default=[],
        help="Path to a CRML attack catalog YAML file (repeatable)",
    )
    exp.add_argument(
        "--control-relationships",
        action="append",
        default=[],
        help="Path to a CRML control relationships YAML file (repeatable)",
    )
    exp.add_argument(
        "--attack-control-relationships",
        action="append",
        default=[],
        help="Path to a CRML attack-control relationships YAML file (repeatable)",
    )

    imp = sub.add_parser("import-xlsx", help="Import an XLSX workbook to CRML YAML documents")
    imp.add_argument("--in", dest="in_path", required=True, help="Input XLSX file path")
    imp.add_argument("--out-dir", required=True, help="Directory to write YAML files")
    imp.add_argument("--overwrite", action="store_true", help="Overwrite existing YAML outputs")
    imp.add_argument("--sort-keys", action="store_true", help="Sort YAML keys")

    return p


def main(argv: list[str] | None = None) -> int:
    try:
        args = _build_parser().parse_args(argv)

        if args.cmd == "export-xlsx":
            catalogs = [CRControlCatalog.load_from_yaml(p) for p in args.control_catalog]
            attack_catalogs = [CRAttackCatalog.load_from_yaml(p) for p in args.attack_catalog]
            rels = [CRControlRelationships.load_from_yaml(p) for p in args.control_relationships]
            attck_rels = [
                CRAttackControlRelationships.load_from_yaml(p) for p in args.attack_control_relationships
            ]

            export_xlsx(
                args.out,
                control_catalogs=catalogs,
                attack_catalogs=attack_catalogs,
                control_relationships=rels,
                attack_control_relationships=attck_rels,
            )
            return 0

        if args.cmd == "import-xlsx":
            imported = import_xlsx(args.in_path)
            written = write_imported_as_yaml(
                imported,
                args.out_dir,
                overwrite=bool(args.overwrite),
                sort_keys=bool(args.sort_keys),
            )
            for p in written:
                print(p)
            return 0

        raise AssertionError(f"Unhandled cmd: {args.cmd}")
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        return 130
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
