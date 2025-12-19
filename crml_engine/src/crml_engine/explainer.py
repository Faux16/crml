import yaml
import sys

def explain_crml(file_path):
    """Parse a CRML scenario file and print a human-readable summary.

    This is a lightweight helper used by the CLI `explain` command.

    Args:
        file_path: Path to a CRML scenario YAML file.

    Returns:
        True if the file could be read and appears to be a CRML scenario,
        otherwise False.

    Side effects:
        Writes a formatted summary to stdout.
    """
    try:
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return False

    if not data or 'crml_scenario' not in data:
        print(f"Error: {file_path} is not a valid CRML scenario document.")
        return False

    meta = data.get('meta', {})
    scenario = data.get('scenario')
    
    print("=== CRML Model Explanation ===")
    print(f"Name:        {meta.get('name', 'N/A')}")
    print(f"Description: {meta.get('description', 'N/A')}")
    print(f"Version:     {meta.get('version', data.get('crml_scenario', 'N/A'))}")
    print("-" * 30)

    if not isinstance(scenario, dict):
        print("No 'scenario' payload found.")
        return False

    freq = scenario.get('frequency', {})
    print(f"Frequency:   {freq.get('model', 'N/A')}")
    params = freq.get('parameters', {})
    if isinstance(params, dict):
        for k, v in params.items():
            print(f"  - {k}: {v}")

    sev = scenario.get('severity', {})
    print(f"Severity:    {sev.get('model', 'N/A')}")
    params = sev.get('parameters', {})
    if isinstance(params, dict):
        for k, v in params.items():
            print(f"  - {k}: {v}")

    print("==============================")
    return True
