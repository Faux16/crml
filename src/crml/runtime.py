import yaml
import numpy as np
import json
import time
import math
from typing import Dict, Any, Union, Optional

# Default currency data structure
# Contains symbol and FX rate for each currency.
#
# IMPORTANT: Rate convention is "1 unit of currency = X USD"
#   - Example: EUR rate 1.08 means 1 EUR = 1.08 USD (euro stronger than dollar)
#   - Example: JPY rate 0.0066 means 1 JPY = 0.0066 USD
#   - To convert: price_usd = amount * CURRENCIES[currency]["rate"]
#
# Rates are approximate as of December 2025 - users can provide their own fx_context for accuracy
CURRENCIES = {
    "USD": {"symbol": "$",   "rate": 1.0},       # US Dollar (base currency)
    "EUR": {"symbol": "€",   "rate": 1.16},      # Euro
    "GBP": {"symbol": "£",   "rate": 1.02},      # British Pound
    "CHF": {"symbol": "Fr",  "rate": 1.09},      # Swiss Franc
    "JPY": {"symbol": "¥",   "rate": 0.0064},    # Japanese Yen
    "CNY": {"symbol": "CN¥", "rate": 0.142},     # Chinese Yuan
    "CAD": {"symbol": "C$",  "rate": 0.72},      # Canadian Dollar
    "AUD": {"symbol": "A$",  "rate": 0.66},      # Australian Dollar
    "INR": {"symbol": "₹",   "rate": 0.0111},    # Indian Rupee
    "BRL": {"symbol": "R$",  "rate": 0.18},      # Brazilian Real
    "PKR": {"symbol": "₨",   "rate": 0.0036},    # Pakistani Rupee
    "MXN": {"symbol": "MX$", "rate": 0.055},     # Mexican Peso
    "KRW": {"symbol": "₩",   "rate": 0.00068},   # South Korean Won
    "SGD": {"symbol": "S$",  "rate": 0.77},      # Singapore Dollar
    "HKD": {"symbol": "HK$", "rate": 0.129},     # Hong Kong Dollar
}

# Derived mappings
DEFAULT_FX_RATES = {code: info["rate"] for code, info in CURRENCIES.items()}
CURRENCY_SYMBOL_TO_CODE = {info["symbol"]: code for code, info in CURRENCIES.items()}
CURRENCY_CODE_TO_SYMBOL = {code: info["symbol"] for code, info in CURRENCIES.items()}


def parse_number(value: Union[str, int, float]) -> float:
    """
    Parse a numeric value that may contain space-separated thousands.
    
    Supports ISO 80000-1 standard thin space (U+202F) and regular space as
    thousands separators for improved readability of large numbers.
    Commas or points are not supported, as they are used differently in various locales as decimal separators.
    
    This is intended for large monetary values like `median` and `scale`,
    NOT for mathematical factors like `mu`, `sigma`, `lambda`, or `shape`.
    
    Examples:
        parse_number(100000) -> 100000.0
        parse_number("100 000") -> 100000.0
        parse_number("1 000 000") -> 1000000.0
        parse_number("100000") -> 100000.0
        
    Args:
        value: A number or string representation that may contain spaces
        
    Returns:
        The parsed float value
    """
    if isinstance(value, (int, float)):
        return float(value)
    # Remove regular spaces and thin spaces (U+202F) used as thousands separators
    cleaned = str(value).replace(' ', '').replace('\u202f', '')
    return float(cleaned)


def calibrate_lognormal_from_single_losses(
    single_losses: list,
    currency: Optional[str],
    base_currency: str,
    fx_config: Dict[str, Any],
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

    sev_currency = currency or fx_config.get('base_currency', 'USD')
    parsed_losses = [parse_number(v) for v in single_losses]
    parsed_losses = [convert_currency(v, sev_currency, base_currency, fx_config) for v in parsed_losses]

    if any(v <= 0 for v in parsed_losses):
        raise ValueError("single_losses values must be positive")

    median_val = float(np.median(parsed_losses))
    mu_val = math.log(median_val)
    log_losses = [math.log(v) for v in parsed_losses]
    sigma_val = float(np.std(log_losses))
    if sigma_val <= 0:
        raise ValueError("Calibrated sigma must be positive")
    return mu_val, sigma_val


def load_fx_config(fx_config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load FX configuration from a YAML file or return defaults.
    
    Args:
        fx_config_path: Path to FX config YAML file (optional)
        
    Returns:
        FX configuration dict with base_currency, output_currency, and rates
    """
    default_config = {
        "base_currency": "USD",
        "output_currency": "USD",
        "rates": DEFAULT_FX_RATES
    }
    
    if fx_config_path is None:
        return default_config
    
    try:
        with open(fx_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Merge with defaults
        result = default_config.copy()
        if config:
            result["base_currency"] = config.get("base_currency", "USD")
            result["output_currency"] = config.get("output_currency", result["base_currency"])
            if "rates" in config:
                result["rates"] = {**DEFAULT_FX_RATES, **config["rates"]}
            result["as_of"] = config.get("as_of")
        return result
    except Exception as e:
        print(f"Warning: Could not load FX config from {fx_config_path}: {e}")
        return default_config


def get_currency_symbol(currency: str) -> str:
    """
    Get the display symbol for a currency code.
    If already a symbol or unknown code, returns the input unchanged.
    """
    return CURRENCY_CODE_TO_SYMBOL.get(currency.upper(), currency)


def convert_currency(amount: float, from_currency: str, to_currency: str, fx_config: Optional[Dict] = None) -> float:
    """
    Convert a monetary amount between currencies.
    
    Args:
        amount: The monetary amount to convert
        from_currency: Source currency code
        to_currency: Target currency code
        fx_config: FX configuration with rates
        
    Returns:
        The converted amount in the target currency
    """
    if fx_config is None:
        fx_config = {"base_currency": "USD", "rates": DEFAULT_FX_RATES}
    
    rates = fx_config.get("rates", DEFAULT_FX_RATES)
    
    # Convert symbol to code if needed
    if from_currency in CURRENCY_SYMBOL_TO_CODE:
        from_currency = CURRENCY_SYMBOL_TO_CODE[from_currency]
    if to_currency in CURRENCY_SYMBOL_TO_CODE:
        to_currency = CURRENCY_SYMBOL_TO_CODE[to_currency]
    
    # If same currency, no conversion needed
    if from_currency == to_currency:
        return amount
    
    # Get rates (rates are value of 1 unit in USD)
    from_rate = rates.get(from_currency, 1.0)
    to_rate = rates.get(to_currency, 1.0)
    
    # Convert: amount in from_currency -> USD -> to_currency
    usd_amount = amount * from_rate
    return usd_amount / to_rate


def normalize_currency(amount: float, from_currency: str, fx_context: Optional[Dict] = None) -> float:
    """
    Normalize a monetary amount to the base currency.
    
    Args:
        amount: The monetary amount to normalize
        from_currency: The currency code or symbol of the amount
        fx_context: Optional FX context with base_currency and rates
        
    Returns:
        The normalized amount in the base currency
    """
    if fx_context is None:
        # Default to USD as base, use default rates
        fx_context = {"base_currency": "USD", "rates": DEFAULT_FX_RATES}
    
    base_currency = fx_context.get("base_currency", "USD")
    rates = fx_context.get("rates", DEFAULT_FX_RATES)
    
    # Convert symbol to code if needed
    if from_currency in CURRENCY_SYMBOL_TO_CODE:
        from_currency = CURRENCY_SYMBOL_TO_CODE[from_currency]
    
    # If already in base currency, no conversion needed
    if from_currency == base_currency:
        return amount
    
    # Get the rate for the from_currency (rate is how much 1 unit of from_currency is worth in base)
    if from_currency in rates:
        rate = rates[from_currency]
        return amount * rate
    
    # If rate not found, assume no conversion
    return amount


def run_simulation(yaml_content: Union[str, dict], n_runs: int = 10000, seed: int = None, fx_config: Optional[Dict] = None) -> Dict[str, Any]:
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
        fx_config = {
            "base_currency": "USD",
            "output_currency": "USD",
            "rates": DEFAULT_FX_RATES
        }
    else:
        # Ensure rates are populated with defaults if not provided
        if fx_config.get("rates") is None:
            fx_config["rates"] = DEFAULT_FX_RATES
    
    base_currency = fx_config.get("base_currency", "USD")
    output_currency = fx_config.get("output_currency", base_currency)
    output_symbol = get_currency_symbol(output_currency)
    
    # Set random seed if provided
    if seed is not None:
        np.random.seed(seed)
    
    result = {
        "success": False,
        "metrics": {},
        "distribution": {},
        "metadata": {"runs": n_runs, "seed": seed, "currency": output_symbol, "currency_code": output_currency},
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
            ln_params = first_component['lognormal']
            if 'single_losses' in ln_params:
                if any(k in ln_params for k in ('median', 'mu', 'sigma')):
                    result["errors"].append("When using 'single_losses', do not also set 'median', 'mu', or 'sigma'.")
                    return result
                try:
                    mu_val, sigma_val = calibrate_lognormal_from_single_losses(
                        ln_params['single_losses'],
                        ln_params.get('currency'),
                        base_currency,
                        fx_config,
                    )
                except (ValueError, TypeError) as e:
                    result["errors"].append(str(e))
                    return result
            else:
                # Support both median and mu (median is preferred)
                if 'median' in ln_params:
                    median_val = parse_number(ln_params['median'])
                    # Default to base currency (USD) if not specified
                    sev_currency = ln_params.get('currency', fx_config.get('base_currency', 'USD'))
                    # Convert from model currency to base currency (simulation currency)
                    median_val = convert_currency(median_val, sev_currency, base_currency, fx_config)
                    if median_val <= 0:
                        result["errors"].append("Median parameter must be positive")
                        return result
                    mu_val = math.log(median_val)
                elif 'mu' in ln_params:
                    # If 'mu' is provided alongside a currency, interpret it as ln(median)
                    # in that currency and shift it into base currency.
                    sev_currency = ln_params.get('currency', fx_config.get('base_currency', 'USD'))
                    mu_in = float(ln_params['mu'])
                    if sev_currency != base_currency:
                        factor = convert_currency(1.0, sev_currency, base_currency, fx_config)
                        mu_val = mu_in + math.log(factor)
                    else:
                        mu_val = mu_in
                else:
                    result["errors"].append("Lognormal distribution requires either 'median' or 'mu' parameter")
                    return result
                if 'sigma' not in ln_params:
                    result["errors"].append("Lognormal distribution requires 'sigma' (or provide 'single_losses' for auto-calibration)")
                    return result
                sigma_val = float(ln_params['sigma'])
        elif 'gamma' in first_component:
            sev_model = 'gamma'
            sev_shape = float(first_component['gamma']['shape'])
            sev_scale = parse_number(first_component['gamma']['scale'])
        else:
            result["errors"].append("Unsupported mixture component")
            return result
    elif sev_model not in ['lognormal', 'gamma']:
        result["errors"].append(f"Unsupported severity model: '{sev_model}'. Supported: lognormal, gamma, mixture")
        return result
    else:
        try:
            if sev_model == 'lognormal':
                params = sev['parameters']
                if 'single_losses' in params:
                    if any(k in params for k in ('median', 'mu', 'sigma')):
                        result["errors"].append("When using 'single_losses', do not also set 'median', 'mu', or 'sigma'.")
                        return result
                    try:
                        mu_val, sigma_val = calibrate_lognormal_from_single_losses(
                            params['single_losses'],
                            params.get('currency'),
                            base_currency,
                            fx_config,
                        )
                    except (ValueError, TypeError) as e:
                        result["errors"].append(str(e))
                        return result
                else:
                    # Support both median and mu (median is preferred)
                    if 'median' in params:
                        median_val = parse_number(params['median'])
                        # Default to base currency (USD) if not specified
                        sev_currency = params.get('currency', fx_config.get('base_currency', 'USD'))
                        # Convert from model currency to base currency (simulation currency)
                        median_val = convert_currency(median_val, sev_currency, base_currency, fx_config)
                        if median_val <= 0:
                            result["errors"].append("Median parameter must be positive")
                            return result
                        mu_val = math.log(median_val)
                    elif 'mu' in params:
                        # If 'mu' is provided alongside a currency, interpret it as ln(median)
                        # in that currency and shift it into base currency.
                        sev_currency = params.get('currency', fx_config.get('base_currency', 'USD'))
                        mu_in = float(params['mu'])
                        if sev_currency != base_currency:
                            factor = convert_currency(1.0, sev_currency, base_currency, fx_config)
                            mu_val = mu_in + math.log(factor)
                        else:
                            mu_val = mu_in
                    else:
                        result["errors"].append("Lognormal distribution requires either 'median' or 'mu' (or provide 'single_losses' for auto-calibration)")
                        return result
                    if 'sigma' not in params:
                        result["errors"].append("Lognormal distribution requires 'sigma' (or provide 'single_losses' for auto-calibration)")
                        return result
                    sigma_val = float(params['sigma'])
                    if sigma_val <= 0:
                        result["errors"].append("Sigma parameter must be positive")
                        return result
            elif sev_model == 'gamma':
                sev_shape = float(sev['parameters']['shape'])
                sev_scale = parse_number(sev['parameters']['scale'])
                sev_currency = sev['parameters'].get('currency', fx_config.get('base_currency', 'USD'))
                sev_scale = convert_currency(sev_scale, sev_currency, base_currency, fx_config)
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

        # Convert losses from base currency (simulation) into output currency for reporting
        if base_currency != output_currency:
            factor = convert_currency(1.0, base_currency, output_currency, fx_config)
            annual_losses = annual_losses * factor

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
    curr = meta.get('currency', '$')
    curr_code = meta.get('currency_code', 'USD')
    
    print(f"\n{'='*50}")
    print(f"CRML Simulation Results")
    print(f"{'='*50}")
    print(f"Model: {meta['model_name']}")
    print(f"Runs: {meta['runs']:,}")
    print(f"Runtime: {meta['runtime_ms']:.2f} ms")
    if meta.get('seed'):
        print(f"Seed: {meta['seed']}")
    print(f"Currency: {curr_code} ({curr})")
    print(f"\n{'='*50}")
    print(f"Risk Metrics")
    print(f"{'='*50}")
    print(f"EAL (Expected Annual Loss):  {curr}{metrics['eal']:,.2f}")
    print(f"VaR 95%:                      {curr}{metrics['var_95']:,.2f}")
    print(f"VaR 99%:                      {curr}{metrics['var_99']:,.2f}")
    print(f"VaR 99.9%:                    {curr}{metrics['var_999']:,.2f}")
    print(f"\nMin Loss:                     {curr}{metrics['min']:,.2f}")
    print(f"Max Loss:                     {curr}{metrics['max']:,.2f}")
    print(f"Median Loss:                  {curr}{metrics['median']:,.2f}")
    print(f"Std Deviation:                {curr}{metrics['std_dev']:,.2f}")
    print(f"{'='*50}\n")
    
    return True
