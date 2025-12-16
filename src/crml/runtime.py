import numpy as np
import json
import time
import math
from typing import Union, Optional
from .models.crml_model import load_crml_from_yaml_str, CRMLSchema
from .models.result_model import SimulationResult, Metrics, Distribution, Metadata
from .models.fx_model import FXConfig, convert_currency, get_currency_symbol, load_fx_config, normalize_fx_config
from .models.constants import DEFAULT_FX_RATES

def calibrate_lognormal_from_single_losses(
    single_losses: list,
    currency: Optional[str],
    base_currency: str,
    fx_config: FXConfig,
) -> tuple[float, float]:
    """Calibrate lognormal mu/sigma from a list of single-event loss amounts.

    Computes:
      mu = ln(median(single_losses))
      sigma = stddev(ln(single_losses))

    Returns:
      (mu, sigma)
    """
    if not isinstance(single_losses, list) or len(single_losses) < 2:
        raise ValueError("single_losses must be an array with at least 2 values")

    sev_currency = currency or fx_config.base_currency
    single_losses = [convert_currency(v, sev_currency, base_currency, fx_config) for v in single_losses]

    if any(v <= 0 for v in single_losses):
        raise ValueError("single_losses values must be positive")

    median_val = float(np.median(single_losses))
    mu_val = math.log(median_val)
    log_losses = [math.log(v) for v in single_losses]
    sigma_val = float(np.std(log_losses))
    if sigma_val <= 0:
        raise ValueError("Calibrated sigma must be positive")
    return mu_val, sigma_val



def run_simulation(yaml_content: Union[str, dict], n_runs: int = 10000, seed: int = None, fx_config: Optional[FXConfig] = None) -> SimulationResult:
    """
    Runs a Monte Carlo simulation based on the CRML model.
    
    Args:
        yaml_content: Either a file path (str) or YAML content (str) or parsed dict
        n_runs: Number of Monte Carlo iterations
        seed: Random seed for reproducibility
        fx_config: FX configuration dict with base_currency, output_currency, and rates
        
    Returns:
        Dictionary with simulation results:
        {
            "success": bool,
            "metrics": {"eal": float, "var_95": float, "var_99": float, "var_999": float},
            "distribution": {"bins": [...], "frequencies": [...], "raw_data": [...]},
            "metadata": {"runs": int, "runtime_ms": float, "model_name": str, "seed": int, "currency": str},
            "errors": []
        }
    """
    start_time = time.time()
    
    # Set default FX config if not provided
    if fx_config is None:
        fx_config = FXConfig(base_currency="USD", output_currency="USD", rates=DEFAULT_FX_RATES)
    elif isinstance(fx_config, dict):
        # Ensure 'rates' is present and valid
        fx_config = dict(fx_config)  # make a copy to avoid mutating input
        if 'rates' not in fx_config or not isinstance(fx_config['rates'], dict):
            fx_config['rates'] = DEFAULT_FX_RATES
        fx_config = FXConfig(**fx_config)  # Convert dict to FXConfig object

    fx_config = normalize_fx_config(fx_config)
    base_currency = fx_config.base_currency
    output_currency = fx_config.output_currency or base_currency
    output_symbol = get_currency_symbol(output_currency)
    
    # Set random seed if provided
    if seed is not None:
        np.random.seed(seed)
    
    result = SimulationResult(
        success=False,
        metrics=Metrics(),
        distribution=Distribution(),
        metadata=Metadata(
            runs=n_runs,
            seed=seed,
            currency=output_symbol,
            currency_code=output_currency
        ),
        errors=[]
    )
    
    try:
        # Accept file path, YAML string, or dict
        if isinstance(yaml_content, str):
            # Check if this is a file path
            import os
            if os.path.isfile(yaml_content):
                import yaml as _yaml
                with open(yaml_content, 'r', encoding='utf-8') as f:
                    yaml_str = f.read()
                crml_obj = load_crml_from_yaml_str(yaml_str)
            else:
                crml_obj = load_crml_from_yaml_str(yaml_content)
        elif isinstance(yaml_content, dict):
            crml_obj = CRMLSchema.model_validate(yaml_content)
        else:
            result.errors.append("Invalid input type. Expected file path, YAML string, or dict.")
            return result
    except Exception as e:
        result.errors.append(f"CRML parsing/validation error: {str(e)}")
        return result

    # Work with the CRML object directly
    model = crml_obj.model
    if not model:
        result.errors.append("Missing 'model' section in CRML document.")
        return result
    assets = model.assets
    freq = model.frequency
    sev = model.severity

    # Get model metadata
    meta = crml_obj.meta
    model_name = meta.name
    result.metadata.model_name = model_name
    result.metadata.model_version = meta.version if meta and hasattr(meta, 'version') else 'N/A'
    result.metadata.description = meta.description if meta and hasattr(meta, 'description') else ''

    # Validate and extract frequency parameters
    freq_model = freq.model if freq and hasattr(freq, 'model') else ''
    if freq_model not in ['poisson', 'gamma', 'hierarchical_gamma_poisson']:
        result.errors.append(f"Unsupported frequency model: '{freq_model}'. Supported: poisson, gamma, hierarchical_gamma_poisson")
        return result

    try:
        params = freq.parameters if freq and hasattr(freq, 'parameters') else None
        if freq_model == 'poisson':
            lambda_val = float(params.lambda_) if params and params.lambda_ is not None else None
            if not lambda_val or lambda_val <= 0:
                result["errors"].append("Lambda parameter must be positive")
                return result
        elif freq_model == 'gamma':
            shape_val = float(params.shape) if params and params.shape is not None else None
            scale_val = float(params.scale) if params and params.scale is not None else None
            if not shape_val or not scale_val | shape_val <= 0 | scale_val <= 0:
                result["errors"].append("Gamma shape and scale must be positive")
                return result
        elif freq_model == 'hierarchical_gamma_poisson':
            alpha_base = float(params.alpha_base) if params and params.alpha_base is not None else 1.5
            beta_base = float(params.beta_base) if params and params.beta_base is not None else 1.5
            shape_val = float(alpha_base)
            scale_val = float(beta_base)
    except (AttributeError, ValueError, TypeError) as e:
        result.errors.append(f"Error extracting frequency parameters: {str(e)}")
        return result

    # Apply control effectiveness if controls are defined
    controls_result = None
    lambda_baseline = lambda_val if freq_model == 'poisson' else None

    if model.controls is not None:
        from crml.controls import apply_control_effectiveness
        # Only apply to Poisson models for now (most common)
        if freq_model == 'poisson':
            controls_result = apply_control_effectiveness(
                base_lambda=lambda_val,
                controls_config=model.controls.model_dump() if hasattr(model.controls, 'model_dump') else model.controls
            )
            # Store baseline for comparison
            result.metadata.lambda_baseline = lambda_val
            result.metadata.controls_applied = True
            # Use effective lambda for simulation
            lambda_val = controls_result['effective_lambda']
            result.metadata.lambda_effective = lambda_val
            result.metadata.control_reduction_pct = controls_result['reduction_pct']
            result.metadata.control_details = controls_result['control_details']
            # Add warnings if any
            if controls_result['warnings']:
                result.metadata.control_warnings = controls_result['warnings']
        else:
            result.metadata.controls_applied = False
            result.metadata.control_warning = f"Controls not yet supported for {freq_model} frequency model"
    else:
        result.metadata.controls_applied = False

    # Validate and extract severity parameters
    sev_model = sev.model if sev and hasattr(sev, 'model') else ''

    # Handle mixture models
    if sev_model == 'mixture':
        components = sev.components if hasattr(sev, 'components') and sev.components else []
        if not components:
            result.errors.append("Mixture model requires at least one component")
            return result
        first_component = components[0]
        if 'lognormal' in first_component:
            sev_model = 'lognormal'
            ln_params = first_component['lognormal']
            if 'single_losses' in ln_params:
                if any(k in ln_params for k in ('median', 'mu', 'sigma')):
                    result.errors.append("When using 'single_losses', do not also set 'median', 'mu', or 'sigma'.")
                    return result
                try:
                    mu_val, sigma_val = calibrate_lognormal_from_single_losses(
                        ln_params['single_losses'],
                        ln_params.get('currency'),
                        base_currency,
                        fx_config,
                    )
                except (ValueError, TypeError) as e:
                    result.errors.append(str(e))
                    return result
            else:
                if 'median' in ln_params:
                    median_val = ln_params['median']
                    sev_currency = ln_params.get('currency', fx_config.base_currency)
                    # Ensure median_val is a float, even if string with spaces/commas
                    try:
                        median_val = float(str(median_val).replace(' ', '').replace(',', ''))
                    except Exception:
                        result.errors.append(f"Median parameter could not be converted to a number: {median_val}")
                        return result
                    median_val = convert_currency(median_val, sev_currency, base_currency, fx_config)
                    if median_val <= 0:
                        result.errors.append("Median parameter must be positive")
                        return result
                    mu_val = math.log(median_val)
                elif 'mu' in ln_params:
                    sev_currency = ln_params.get('currency', fx_config.base_currency)
                    mu_in = float(ln_params['mu'])
                    if sev_currency != base_currency:
                        factor = convert_currency(1.0, sev_currency, base_currency, fx_config)
                        mu_val = mu_in + math.log(factor)
                    else:
                        mu_val = mu_in
                else:
                    result.errors.append("Lognormal distribution requires either 'median' or 'mu' parameter")
                    return result
                if 'sigma' not in ln_params:
                    result.errors.append("Lognormal distribution requires 'sigma' (or provide 'single_losses' for auto-calibration)")
                    return result
                sigma_val = float(ln_params['sigma'])
        elif 'gamma' in first_component:
            sev_model = 'gamma'
            sev_shape = float(first_component['gamma']['shape'])
            sev_scale = first_component['gamma']['scale']
        else:
            result.errors.append("Unsupported mixture component")
            return result
    elif sev_model not in ['lognormal', 'gamma']:
        result.errors.append(f"Unsupported severity model: '{sev_model}'. Supported: lognormal, gamma, mixture")
        return result
    else:
        try:
            params = sev.parameters if sev and hasattr(sev, 'parameters') else None
            if sev_model == 'lognormal':
                if params and params.single_losses is not None:
                    if any(getattr(params, k, None) is not None for k in ('median', 'mu', 'sigma')):
                        result.errors.append("When using 'single_losses', do not also set 'median', 'mu', or 'sigma'.")
                        return result
                    try:
                        mu_val, sigma_val = calibrate_lognormal_from_single_losses(
                            params.single_losses,
                            params.currency,
                            base_currency,
                            fx_config,
                        )
                    except (ValueError, TypeError) as e:
                        result.errors.append(str(e))
                        return result
                else:
                    # Reject if both median and mu are provided
                    if params and params.median is not None and params.mu is not None:
                        result.errors.append("Cannot use both 'median' and 'mu'. Choose one (median is recommended).")
                        return result
                    if params and params.median is not None:
                        median_val = params.median
                        sev_currency = params.currency if params.currency is not None else fx_config.base_currency
                        # Ensure median_val is a float, even if string with spaces/commas
                        try:
                            median_val = float(str(median_val).replace(' ', '').replace(',', ''))
                        except Exception:
                            result.errors.append(f"Median parameter could not be converted to a number: {median_val}")
                            return result
                        median_val = convert_currency(median_val, sev_currency, base_currency, fx_config)
                        if median_val <= 0:
                            result.errors.append("Median parameter must be positive")
                            return result
                        mu_val = math.log(median_val)
                    elif params and params.mu is not None:
                        sev_currency = params.currency if params.currency is not None else fx_config.base_currency
                        mu_in = float(params.mu)
                        if sev_currency != base_currency:
                            factor = convert_currency(1.0, sev_currency, base_currency, fx_config)
                            mu_val = mu_in + math.log(factor)
                        else:
                            mu_val = mu_in
                    else:
                        result.errors.append("Lognormal distribution requires either 'median' or 'mu' (or provide 'single_losses' for auto-calibration)")
                        return result
                    if not params or params.sigma is None:
                        result.errors.append("Lognormal distribution requires 'sigma' (or provide 'single_losses' for auto-calibration)")
                        return result
                    sigma_val = float(params.sigma)
                    if sigma_val <= 0:
                        result.errors.append("Sigma parameter must be positive")
                        return result
            elif sev_model == 'gamma':
                sev_shape = float(params.shape) if params and params.shape is not None else None
                sev_scale = params.scale if params and params.scale is not None else None
                sev_currency = params.currency if params and params.currency is not None else fx_config.base_currency
                sev_scale = convert_currency(sev_scale, sev_currency, base_currency, fx_config)
                if not sev_shape or not sev_scale | sev_shape <= 0 | sev_scale <= 0:
                    result.errors.append("Gamma shape and scale must be positive")
                    return result
        except (AttributeError, ValueError, TypeError) as e:
            result.errors.append(f"Error extracting severity parameters: {str(e)}")
            return result

    # Extract total asset cardinality (sum over all assets)
    try:
        cardinality = sum(int(asset.cardinality) for asset in assets) if assets else 1
        if cardinality <= 0:
            result.errors.append("Asset cardinality must be positive")
            return result
    except (ValueError, TypeError, AttributeError) as e:
        result.errors.append(f"Invalid asset cardinality: {str(e)}")
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

        # Convert losses from base currency (simulation) into output currency for reporting
        if base_currency != output_currency:
            factor = convert_currency(1.0, base_currency, output_currency, fx_config)
            annual_losses = annual_losses * factor

        # Calculate metrics
        eal = float(np.mean(annual_losses))
        var_95 = float(np.percentile(annual_losses, 95))
        var_99 = float(np.percentile(annual_losses, 99))
        var_999 = float(np.percentile(annual_losses, 99.9))
        
        result.metrics = Metrics(
            eal=eal,
            var_95=var_95,
            var_99=var_99,
            var_999=var_999,
            min=float(np.min(annual_losses)),
            max=float(np.max(annual_losses)),
            median=float(np.median(annual_losses)),
            std_dev=float(np.std(annual_losses))
        )

        # Create histogram for distribution
        # Use 50 bins for visualization
        hist, bin_edges = np.histogram(annual_losses, bins=50)
        result.distribution = Distribution(
            bins=bin_edges.tolist(),
            frequencies=hist.tolist(),
            raw_data=annual_losses.tolist()[:1000]
        )

        # Calculate runtime
        runtime_ms = (time.time() - start_time) * 1000
        result.metadata.runtime_ms = runtime_ms
        result.success = True

    except Exception as e:
        result.errors.append(f"Simulation error: {str(e)}")
        return result

    return result


def run_simulation_cli(file_path: str, n_runs: int = 10000, output_format: str = 'text', fx_config_path: Optional[str] = None):
    """
    CLI wrapper for run_simulation that prints results.
    
    Args:
        file_path: Path to CRML YAML file
        n_runs: Number of simulation runs
        output_format: 'text' or 'json'
        fx_config_path: Path to FX configuration YAML file (optional)
    """
    # Load FX config
    fx_config = load_fx_config(fx_config_path)
    result = run_simulation(file_path, n_runs, fx_config=fx_config)

    if output_format == 'json':
        # Use model_dump for pretty JSON output
        print(json.dumps(result.model_dump(), indent=2))
        return result.success

    # Text output
    from .models.result_model import print_result
    print_result(result)
    return result.success
