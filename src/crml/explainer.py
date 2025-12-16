import yaml
import sys

def explain_crml(file_path):
    """
    Parses a CRML file and prints a human-readable summary.
    """
    try:
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return False

    if not data or 'crml' not in data:
        print(f"Error: {file_path} is not a valid CRML document.")
        return False

    meta = data.get('meta', {})
    model = data.get('model', {})
    
    print("=== CRML Model Explanation ===")
    print(f"Name:        {meta.get('name', 'N/A')}")
    print(f"Description: {meta.get('description', 'N/A')}")
    print(f"Version:     {meta.get('version', data.get('crml', 'N/A'))}")
    print("-" * 30)
    
    entities = model.get('entities', {})
    print(f"Entities:    {entities.get('count', 'N/A')}")

    freq = model.get('frequency', {})
    print(f"Frequency:   {freq.get('type', 'N/A')}")
    params = freq.get('params', {})
    for k, v in params.items():
        print(f"  - {k}: {v}")

    sev = model.get('severity', {})
    print(f"Severity:    {sev.get('type', 'N/A')}")
    params = sev.get('params', {})
    for k, v in params.items():
        print(f"  - {k}: {v}")

    print("==============================")
    return True
