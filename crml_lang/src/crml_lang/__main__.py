from __future__ import annotations

import argparse
import sys
from typing import Optional

from .cli import bundle_portfolio_to_yaml, validate_to_text


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

        raise AssertionError(f"Unhandled cmd: {args.cmd}")
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
