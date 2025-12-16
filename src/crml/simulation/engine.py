"""
Core Monte Carlo simulation engine for CRML.
"""
import time
import numpy as np
from typing import Union, Optional, Dict, List

from ..models.crml_model import load_crml_from_yaml_str, CRMLSchema
from ..models.result_model import SimulationResult, Metrics, Distribution, Metadata
from ..models.fx_model import FXConfig, convert_currency, get_currency_symbol, normalize_fx_config
from ..models.constants import DEFAULT_FX_RATES
from ..controls import apply_control_effectiveness

from .frequency import FrequencyEngine
from .severity import SeverityEngine

def run_monte_carlo(
    yaml_content: Union[str, dict],
    n_runs: int = 10000,
    seed: int = None,
    fx_config: Optional[FXConfig] = None
) -> SimulationResult:
    """
    Orchestrates the Monte Carlo simulation.
    """
    start_time = time.time()
    
    # 1. Configuration Setup
    if fx_config is None:
        fx_config = FXConfig(base_currency="USD", output_currency="USD", rates=DEFAULT_FX_RATES)
    elif isinstance(fx_config, dict):
        fx_config = dict(fx_config)
        if 'rates' not in fx_config: fx_config['rates'] = DEFAULT_FX_RATES
        fx_config = FXConfig(**fx_config)
        
    fx_config = normalize_fx_config(fx_config)
    output_symbol = get_currency_symbol(fx_config.output_currency)

    if seed is not None:
        np.random.seed(seed)
        
    result = SimulationResult(
        success=False,
        metrics=Metrics(),
        distribution=Distribution(),
        metadata=Metadata(
            runs=n_runs, seed=seed, 
            currency=output_symbol, 
            currency_code=fx_config.output_currency
        ),
        errors=[]
    )

    # 2. Parsing & Validation
    try:
        if isinstance(yaml_content, str):
            import os
            if os.path.isfile(yaml_content):
                with open(yaml_content, 'r', encoding='utf-8') as f:
                    yaml_str = f.read()
                crml_obj = load_crml_from_yaml_str(yaml_str)
            else:
                crml_obj = load_crml_from_yaml_str(yaml_content)
        elif isinstance(yaml_content, dict):
            crml_obj = CRMLSchema.model_validate(yaml_content)
        else:
            result.errors.append("Invalid input type")
            return result
    except Exception as e:
        result.errors.append(f"Parsing error: {str(e)}")
        return result

    model = crml_obj.model
    if not model:
        result.errors.append("Missing 'model' section")
        return result

    # Populating Metadata
    meta = crml_obj.meta
    result.metadata.model_name = meta.name
    result.metadata.model_version = meta.version or 'N/A'
    result.metadata.description = meta.description or ''

    # 3. Execution Setup
    # Currently single-scenario logic (preserving existing behavior + refactoring)
    # TODO: Multi-scenario loop goes here
    
    assets = model.assets
    freq = model.frequency
    sev = model.severity
    
    # Asset Cardinality
    try:
        cardinality = sum(int(asset.cardinality) for asset in assets) if assets else 1
    except Exception as e:
        result.errors.append(f"Invalid asset cardinality: {e}")
        return result
        
    # Controls Application (Heuristic/Multiplicative)
    freq_model = freq.model if freq else ''
    lambda_val = None
    if freq_model == 'poisson' and freq.parameters:
        lambda_val = float(freq.parameters.lambda_) if freq.parameters.lambda_ is not None else 0.0
        
    if model.controls and freq_model == 'poisson' and lambda_val is not None:
        controls_res = apply_control_effectiveness(
            base_lambda=lambda_val,
            controls_config=model.controls.model_dump(),
        )
        result.metadata.controls_applied = True
        result.metadata.lambda_baseline = lambda_val
        lambda_val = controls_res['effective_lambda']
        result.metadata.lambda_effective = lambda_val
        result.metadata.control_reduction_pct = controls_res['reduction_pct']
        result.metadata.control_details = controls_res['control_details']
        if controls_res['warnings']:
            result.metadata.control_warnings = controls_res['warnings']
            
        # Update keys in params for the simulation step
        # Ideally we shouldn't mutate the pydantic object, but for this linear flow:
        # We need to construct a params input that has the NEW lambda
        # Let's create a temporary override dict or modify the params object
        freq.parameters.lambda_ = lambda_val

    # 4. Simulation Loop
    try:
        # A. Frequency
        counts = FrequencyEngine.generate_frequency(
            freq_model=freq_model,
            params=freq.parameters,
            n_runs=n_runs,
            cardinality=cardinality,
            seed=seed
        )
        
        annual_losses = []
        total_events = int(np.sum(counts))
        
        if total_events > 0:
            # B. Severity
            sev_model = sev.model if sev else ''
            severities = SeverityEngine.generate_severity(
                sev_model=sev_model,
                params=sev.parameters,
                components=sev.components,
                total_events=total_events,
                fx_config=fx_config
            )
            
            # C. Aggregation (Sum severities per year)
            # This can be optimized with vectorization (np.add.at or cumsum/diff)
            # For now, keeping the loop for clarity and safety with jagged arrays logic
            
            # Make sure we got enough severities (should be exact)
            if len(severities) != total_events:
                 # Fallback if something went wrong inside severity engine
                 severities = np.zeros(total_events)
            
            # Optimized aggregation
            # Create Run IDs for each event
            # run_indices = np.repeat(np.arange(n_runs), counts)
            # annual_losses_arr = np.bincount(run_indices, weights=severities, minlength=n_runs)
            # annual_losses = annual_losses_arr
            
            current_idx = 0
            for c in counts:
                if c > 0:
                   loss = np.sum(severities[current_idx : current_idx + c])
                   annual_losses.append(loss)
                   current_idx += c
                else:
                   annual_losses.append(0.0)
        else:
            annual_losses = np.zeros(n_runs)
            
        annual_losses = np.array(annual_losses)

        # 5. Reporting Currency Conversion
        if fx_config.base_currency != fx_config.output_currency:
            factor = convert_currency(1.0, fx_config.base_currency, fx_config.output_currency, fx_config)
            annual_losses = annual_losses * factor

        # 6. Metrics Calculation
        eal = float(np.mean(annual_losses))
        result.metrics = Metrics(
            eal=eal,
            var_95=float(np.percentile(annual_losses, 95)),
            var_99=float(np.percentile(annual_losses, 99)),
            var_999=float(np.percentile(annual_losses, 99.9)),
            min=float(np.min(annual_losses)),
            max=float(np.max(annual_losses)),
            median=float(np.median(annual_losses)),
            std_dev=float(np.std(annual_losses))
        )

        hist, bin_edges = np.histogram(annual_losses, bins=50)
        result.distribution = Distribution(
            bins=bin_edges.tolist(),
            frequencies=hist.tolist(),
            raw_data=annual_losses.tolist()[:1000]
        )

        result.metadata.runtime_ms = (time.time() - start_time) * 1000
        result.success = True

    except Exception as e:
        result.errors.append(f"Simulation execution error: {str(e)}")
        # Raise for debugging? No, capture in result object for API consistency.
        
    return result
