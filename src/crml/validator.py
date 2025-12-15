import sys
import json
import yaml
from jsonschema import Draft202012Validator, ValidationError, SchemaError
import os

# Schema is now inside the package at src/crml/schema/crml-schema.json
# This file is at src/crml/validator.py
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema", "crml-schema.json")

def load_schema():
    with open(SCHEMA_PATH, "r") as f:
        return json.load(f)

def validate_crml(path: str) -> bool:
    """
    Validate a CRML file against the JSON Schema (Draft 2020-12).
    Returns True if valid, False otherwise.
    Prints all errors and warnings found.
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

    # Use Draft202012Validator for full JSON Schema 2020-12 support
    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(data))
    
    if not errors:
        # Additional semantic warnings
        warnings = []
        
        # Warn if using old CRML version
        if data.get("crml") != "1.1":
            warnings.append(f"CRML version '{data.get('crml')}' is not current. Consider upgrading to '1.1'.")
        
        # Warn if mixture weights don't sum to 1
        severity = data.get("model", {}).get("severity", {})
        if severity.get("model") == "mixture" and "components" in severity:
            total_weight = 0
            for comp in severity["components"]:
                dist_key = list(comp.keys())[0]
                total_weight += comp[dist_key].get("weight", 0)
            if abs(total_weight - 1.0) > 0.001:
                warnings.append(f"Mixture weights sum to {total_weight:.3f}, should sum to 1.0")
        
        # Warn if no output metrics specified
        output = data.get("output", {})
        if not output.get("metrics"):
            warnings.append("No output metrics specified. Consider adding 'EAL', 'VaR_95', etc.")
        
        print(f"[OK] {path} is a valid CRML 1.1 document.")
        for w in warnings:
            print(f"[WARNING] {w}")
        return True
    else:
        print(f"[ERROR] {path} failed CRML 1.1 validation with {len(errors)} error(s):")
        for i, error in enumerate(errors, 1):
            path_str = " -> ".join(map(str, error.path)) if error.path else "(root)"
            
            # Provide human-friendly error messages
            if error.validator == "const":
                msg = f"Expected '{error.validator_value}', got '{error.instance}'"
            elif error.validator == "oneOf":
                if isinstance(error.instance, dict):
                    # More human-friendly messages for common parameter conflicts
                    if "mu" in error.instance and "median" in error.instance:
                        msg = "Cannot use both 'median' and 'mu'. Choose one (median is recommended)."
                    elif "single_losses" in error.instance and any(k in error.instance for k in ("median", "mu", "sigma")):
                        msg = "When using 'single_losses', do not also set 'median', 'mu', or 'sigma'."
                    elif "single_losses" in error.instance:
                        msg = "'single_losses' must be an array with at least 2 positive values. It replaces median/mu/sigma by auto-calibration."
                    else:
                        msg = error.message
                else:
                    msg = error.message
            elif error.validator == "required":
                msg = f"Missing required property: '{error.validator_value[0]}'"
            elif error.validator == "enum":
                msg = f"Value must be one of: {', '.join(map(str, error.validator_value))}"
            else:
                msg = error.message
            
            print(f"  {i}. [{path_str}] {msg}")
        return False
