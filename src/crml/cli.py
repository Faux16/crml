import argparse
import sys
from crml.validator import validate_crml

def main():
    parser = argparse.ArgumentParser(description="CRML CLI")
    sub = parser.add_subparsers(dest="command")

    v = sub.add_parser("validate", help="Validate a CRML file")
    v.add_argument("file", help="Path to CRML YAML/JSON file")

    args = parser.parse_args()

    if args.command == "validate":
        success = validate_crml(args.file)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
