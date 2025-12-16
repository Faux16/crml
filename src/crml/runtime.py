import json
from typing import Union, Optional
from .models.crml_model import load_crml_from_yaml_str, CRMLSchema
from .models.result_model import SimulationResult, print_result
from .models.fx_model import (
    FXConfig, 
    load_fx_config, 
    normalize_fx_config, 
    convert_currency, 
    get_currency_symbol, 
    DEFAULT_FX_RATES
)
from .simulation.engine import run_monte_carlo
from .simulation.severity import SeverityEngine

# Backward compatibility alias
def run_simulation(
    yaml_content: Union[str, dict], 
    n_runs: int = 10000, 
    seed: int = None, 
    fx_config: Optional[FXConfig] = None
) -> SimulationResult:
    """
    Backward compatible wrapper for run_monte_carlo.
    
    See crml.simulation.engine.run_monte_carlo for documentation.
    """
    return run_monte_carlo(yaml_content, n_runs, seed, fx_config)

def calibrate_lognormal_from_single_losses(
    single_losses: list,
    currency: Optional[str],
    base_currency: str,
    fx_config: FXConfig,
) -> tuple[float, float]:
    """
    Backward compatible wrapper for severity calibration.
    """
    return SeverityEngine.calibrate_lognormal_from_single_losses(
        single_losses, currency, base_currency, fx_config
    )

def run_simulation_cli(file_path: str, n_runs: int = 10000, output_format: str = 'text', fx_config_path: Optional[str] = None):
    """
    CLI wrapper for run_simulation that prints results.
    """
    # Load FX config
    fx_config = load_fx_config(fx_config_path)
    result = run_simulation(file_path, n_runs, fx_config=fx_config)

    if output_format == 'json':
        # Use model_dump for pretty JSON output
        print(json.dumps(result.model_dump(), indent=2))
        return result.success

    # Text output
    print_result(result)
    return result.success
