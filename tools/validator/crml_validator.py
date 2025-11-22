import sys
import json
import yaml
from jsonschema import validate, ValidationError, SchemaError
import os

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "spec", "crml-schema.json")

def load_schema():
    with open(SCHEMA_PATH, "r") as f:
        return json.load(f)

def validate_crml(path: str) -> None:
    schema = load_schema()
    with open(path, "r") as f:
        data = yaml.safe_load(f)

    try:
        validate(instance=data, schema=schema)
        print(f"[OK] {path} is a valid CRML 1.0 document.")
    except SchemaError as e:
        print("[SCHEMA ERROR] Invalid CRML schema definition.")
        print(e)
        sys.exit(2)
    except ValidationError as e:
        print(f"[ERROR] {path} failed CRML 1.0 validation.")
        print("Message:", e.message)
        print("Path:   ", " -> ".join(map(str, e.path)))
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python crml_validator.py <crml-file.yaml>")
        sys.exit(1)
    validate_crml(sys.argv[1])
