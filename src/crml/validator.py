import sys
import json
import yaml
from jsonschema import validate, ValidationError, SchemaError
import os

# Schema is now inside the package at src/crml/schema/crml-schema.json
# This file is at src/crml/validator.py
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema", "crml-schema.json")

def load_schema():
    with open(SCHEMA_PATH, "r") as f:
        return json.load(f)

def validate_crml(path: str) -> bool:
    """
    Validate a CRML file against the schema.
    Returns True if valid, False otherwise.
    """
    try:
        schema = load_schema()
    except FileNotFoundError:
        print(f"[ERROR] Schema file not found at {SCHEMA_PATH}")
        return False

    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"[ERROR] Failed to read or parse file {path}: {e}")
        return False

    try:
        validate(instance=data, schema=schema)
        print(f"[OK] {path} is a valid CRML 1.1 document.")
        return True
    except SchemaError as e:
        print("[SCHEMA ERROR] Invalid CRML schema definition.")
        print(e)
        return False
    except ValidationError as e:
        print(f"[ERROR] {path} failed CRML 1.1 validation.")
        print("Message:", e.message)
        print("Path:   ", " -> ".join(map(str, e.path)))
        return False
