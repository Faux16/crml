#!/usr/bin/env python
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir))
VALIDATOR = os.path.join(ROOT, "tools", "validator", "crml_validator.py")

def main():
    parser = argparse.ArgumentParser(description="CRML CLI")
    sub = parser.add_subparsers(dest="command")

    v = sub.add_parser("validate", help="Validate a CRML file")
    v.add_argument("file", help="Path to CRML YAML/JSON file")

    args = parser.parse_args()

    if args.command == "validate":
        cmd = [sys.executable, VALIDATOR, args.file]
        sys.exit(subprocess.call(cmd))
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
