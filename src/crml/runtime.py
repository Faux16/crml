import yaml
import numpy as np
import json
import time
from typing import Dict, Any, Union

def run_simulation(yaml_content: Union[str, dict], n_runs: int = 10000, seed: int = None) -> Dict[str, Any]:
    """
    Runs a Monte Carlo simulation based on the CRML model.
    
    Args:
        yaml_content: Either a file path (str) or YAML content (str) or parsed dict
        n_runs: Number of Monte Carlo iterations
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary with simulation results:
        {
            "success": bool,
            "metrics": {"eal": float, "var_95": float, "var_99": float, "var_999": float},
            "distribution": {"bins": [...], "frequencies": [...], "raw_data": [...]},
            "metadata": {"runs": int, "runtime_ms": float, "model_name": str, "seed": int},
            "errors": [...]
        }
    """
    start_time = time.time()
    
    # Set random seed if provided
    if seed is not None:
        np.random.seed(seed)
    
    result = {
        "success": False,
        "metrics": {},
        "distribution": {},
        "metadata": {"runs": n_runs, "seed": seed},
        "errors": []
    }
    
    try:
        # Parse YAML if it's a string
        if isinstance(yaml_content, str):
            # Check if it's a file path or YAML content
            if yaml_content.endswith('.yaml') or yaml_content.endswith('.yml'):
                try:
                    with open(yaml_content, 'r') as f:
                        data = yaml.safe_load(f)
                except FileNotFoundError:
                    # Not a file, try parsing as YAML content
                    data = yaml.safe_load(yaml_content)
            else:
                data = yaml.safe_load(yaml_content)
        elif isinstance(yaml_content, dict):
            data = yaml_content
        else:
            result["errors"].append("Invalid input type. Expected file path, YAML string, or dict.")
            return result
            
    except yaml.YAMLError as e:
        result["errors"].append(f"YAML parsing error: {str(e)}")
        return result
    except Exception as e:
        result["errors"].append(f"Error reading input: {str(e)}")
        return result

    # Validate CRML document
    if not data or 'crml' not in data:
        result["errors"].append("Not a valid CRML document. Missing 'crml' version field.")
        return result

    # Extract model components
    model = data.get('model', {})
    if not model:
        result["errors"].append("Missing 'model' section in CRML document.")
        return result
        
    assets = model.get('assets', {})
    freq = model.get('frequency', {})
    sev = model.get('severity', {})

    # Get model metadata
    meta = data.get('meta', {})
    model_name = meta.get('name', 'Unknown Model')
    result["metadata"]["model_name"] = model_name
    result["metadata"]["model_version"] = meta.get('version', 'N/A')
    result["metadata"]["description"] = meta.get('description', '')

    # Validate and extract frequency parameters
    freq_model = freq.get('model', '')
    if freq_model not in ['poisson', 'gamma', 'hierarchical_gamma_poisson']:
        result["errors"].append(f"Unsupported frequency model: '{freq_model}'. Supported: poisson, gamma, hierarchical_gamma_poisson")
        return result

    try:
        if freq_model == 'poisson':
            lambda_val = float(freq['parameters']['lambda'])
            if lambda_val <= 0:
                result["errors"].append("Lambda parameter must be positive")
                return result
        elif freq_model == 'gamma':
            shape_val = float(freq['parameters']['shape'])
            scale_val = float(freq['parameters']['scale'])
            if shape_val <= 0 or scale_val <= 0:
                result["errors"].append("Gamma shape and scale must be positive")
                return result
        elif freq_model == 'hierarchical_gamma_poisson':
            # For hierarchical models, we'll use simplified parameters
            # In production, this would use MCMC sampling
            alpha_base = freq['parameters'].get('alpha_base', 1.0)
            beta_base = freq['parameters'].get('beta_base', 1.0)
            # Parse alpha_base if it's an expression (e.g., "1 + CI * 0.5")
            if isinstance(alpha_base, str):
                # For now, just use default value
                alpha_base = 1.5
            if isinstance(beta_base, str):
                beta_base = 1.5
            # Convert to equivalent simple gamma for Monte Carlo
            shape_val = float(alpha_base)
            scale_val = float(beta_base)
    except (KeyError, ValueError) as e:
        result["errors"].append(f"Error extracting frequency parameters: {str(e)}")
        return result

    # Validate and extract severity parameters
    sev_model = sev.get('model', '')
    
    # Handle mixture models
    if sev_model == 'mixture':
        # For mixture models, use the first component for simplification
        components = sev.get('components', [])
        if not components:
            result["errors"].append("Mixture model requires at least one component")
            return result
        # Use first component (typically the dominant one)
        first_component = components[0]
        if 'lognormal' in first_component:
            sev_model = 'lognormal'
            mu_val = float(first_component['lognormal']['mu'])
            sigma_val = float(first_component['lognormal']['sigma'])
        elif 'gamma' in first_component:
            sev_model = 'gamma'
            sev_shape = float(first_component['gamma']['shape'])
            sev_scale = float(first_component['gamma']['scale'])
        else:
            result["errors"].append("Unsupported mixture component")
            return result
    elif sev_model not in ['lognormal', 'gamma']:
        result["errors"].append(f"Unsupported severity model: '{sev_model}'. Supported: lognormal, gamma, mixture")
        return result
    else:
        try:
            if sev_model == 'lognormal':
                mu_val = float(sev['parameters']['mu'])
                sigma_val = float(sev['parameters']['sigma'])
                if sigma_val <= 0:
                    result["errors"].append("Sigma parameter must be positive")
                    return result
            elif sev_model == 'gamma':
                sev_shape = float(sev['parameters']['shape'])
                sev_scale = float(sev['parameters']['scale'])
                if sev_shape <= 0 or sev_scale <= 0:
                    result["errors"].append("Gamma shape and scale must be positive")
                    return result
        except (KeyError, ValueError) as e:
            result["errors"].append(f"Error extracting severity parameters: {str(e)}")
            return result

    # Extract asset cardinality
    try:
        cardinality = int(assets.get('cardinality', 1))
        if cardinality <= 0:
            result["errors"].append("Asset cardinality must be positive")
            return result
    except (ValueError, TypeError) as e:
        result["errors"].append(f"Invalid asset cardinality: {str(e)}")
        return result

    # Run Monte Carlo simulation
    try:
        annual_losses = []
        
        # Generate frequency (number of events per run)
        if freq_model == 'poisson':
            total_lambda = lambda_val * cardinality
            num_events_per_run = np.random.poisson(total_lambda, n_runs)
        elif freq_model in ['gamma', 'hierarchical_gamma_poisson']:
            # For gamma and hierarchical models, sample and round to integers
            num_events_per_run = np.random.gamma(shape_val, scale_val, n_runs)
            num_events_per_run = np.maximum(0, np.round(num_events_per_run * cardinality)).astype(int)
        
        # Generate severity for all events
        total_events = np.sum(num_events_per_run)
        
        if total_events > 0:
            if sev_model == 'lognormal':
                severities = np.random.lognormal(mu_val, sigma_val, total_events)
            elif sev_model == 'gamma':
                severities = np.random.gamma(sev_shape, sev_scale, total_events)
            
            # Aggregate losses per run
            current_idx = 0
            for n_events in num_events_per_run:
                if n_events > 0:
                    loss = np.sum(severities[current_idx : current_idx + n_events])
                    annual_losses.append(loss)
                    current_idx += n_events
                else:
                    annual_losses.append(0.0)
        else:
            annual_losses = [0.0] * n_runs

        annual_losses = np.array(annual_losses)

        # Calculate metrics
        eal = float(np.mean(annual_losses))
        var_95 = float(np.percentile(annual_losses, 95))
        var_99 = float(np.percentile(annual_losses, 99))
        var_999 = float(np.percentile(annual_losses, 99.9))
        
        result["metrics"] = {
            "eal": eal,
            "var_95": var_95,
            "var_99": var_99,
            "var_999": var_999,
            "min": float(np.min(annual_losses)),
            "max": float(np.max(annual_losses)),
            "median": float(np.median(annual_losses)),
            "std_dev": float(np.std(annual_losses))
        }

        # Create histogram for distribution
        # Use 50 bins for visualization
        hist, bin_edges = np.histogram(annual_losses, bins=50)
        
        result["distribution"] = {
            "bins": bin_edges.tolist(),
            "frequencies": hist.tolist(),
            "raw_data": annual_losses.tolist()[:1000]  # Limit raw data to first 1000 points
        }

        # Calculate runtime
        runtime_ms = (time.time() - start_time) * 1000
        result["metadata"]["runtime_ms"] = runtime_ms
        
        result["success"] = True
        
    except Exception as e:
        result["errors"].append(f"Simulation error: {str(e)}")
        return result

    return result


def run_simulation_cli(file_path: str, n_runs: int = 10000, output_format: str = 'text'):
    """
    CLI wrapper for run_simulation that prints results.
    
    Args:
        file_path: Path to CRML YAML file
        n_runs: Number of simulation runs
        output_format: 'text' or 'json'
    """
    result = run_simulation(file_path, n_runs)
    
    if output_format == 'json':
        print(json.dumps(result, indent=2))
        return result["success"]
    
    # Text output
    if not result["success"]:
        print("❌ Simulation failed:")
        for error in result["errors"]:
            print(f"  • {error}")
        return False
    
    meta = result["metadata"]
    metrics = result["metrics"]
    
    print(f"\n{'='*50}")
    print(f"CRML Simulation Results")
    print(f"{'='*50}")
    print(f"Model: {meta['model_name']}")
    print(f"Runs: {meta['runs']:,}")
    print(f"Runtime: {meta['runtime_ms']:.2f} ms")
    if meta.get('seed'):
        print(f"Seed: {meta['seed']}")
    print(f"\n{'='*50}")
    print(f"Risk Metrics")
    print(f"{'='*50}")
    print(f"EAL (Expected Annual Loss):  ${metrics['eal']:,.2f}")
    print(f"VaR 95%:                      ${metrics['var_95']:,.2f}")
    print(f"VaR 99%:                      ${metrics['var_99']:,.2f}")
    print(f"VaR 99.9%:                    ${metrics['var_999']:,.2f}")
    print(f"\nMin Loss:                     ${metrics['min']:,.2f}")
    print(f"Max Loss:                     ${metrics['max']:,.2f}")
    print(f"Median Loss:                  ${metrics['median']:,.2f}")
    print(f"Std Deviation:                ${metrics['std_dev']:,.2f}")
    print(f"{'='*50}\n")
    
    return True
