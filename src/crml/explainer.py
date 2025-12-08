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
    print(f"Version:     {data.get('crml', 'N/A')}")
    print("-" * 30)
    
    assets = model.get('assets', {})
    print(f"Assets:      {assets.get('cardinality', 'N/A')} entities")
    
    freq = model.get('frequency', {})
    print(f"Frequency:   {freq.get('model', 'N/A')}")
    if 'parameters' in freq:
        for k, v in freq['parameters'].items():
            print(f"  - {k}: {v}")

    sev = model.get('severity', {})
    print(f"Severity:    {sev.get('model', 'N/A')}")
    if 'parameters' in sev:
        for k, v in sev['parameters'].items():
            print(f"  - {k}: {v}")
            
    print("==============================")
    return True
