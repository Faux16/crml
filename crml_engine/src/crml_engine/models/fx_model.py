"""FX config models and loader.

FX config is a separate document type from CRML scenarios/portfolios.
We version it with a top-level `crml_fx_config` field and validate it against
a small JSON Schema to keep CLI behavior deterministic.
"""

from __future__ import annotations

import json
import os
from typing import Dict, Optional

import yaml
from jsonschema import Draft202012Validator
from pydantic import BaseModel, ConfigDict, Field

from .constants import DEFAULT_FX_RATES, CURRENCY_SYMBOL_TO_CODE, CURRENCY_CODE_TO_SYMBOL


FX_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "schemas", "crml-fx-config-schema.json")

class CurrencyInfo(BaseModel):
    symbol: str = Field(..., description="Currency display symbol (e.g. '$', '€').")
    rate: float = Field(..., description="Conversion rate relative to the configured base currency.")


class FXConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    base_currency: str = Field(default="USD", description="Base currency code used for FX rates (typically 'USD').")
    output_currency: str = Field(default="USD", description="Default output/reporting currency code.")
    output_symbol: str = Field(default="$", description="Display symbol for the output currency.")
    rates: Dict[str, float] = Field(..., description="Mapping of currency code to rate relative to base currency.")
    as_of: Optional[str] = Field(None, description="Optional timestamp/date for when rates were observed.")

def get_default_fx_config() -> FXConfig:
    """
    Returns a default FXConfig instance with USD as base/output and default rates.
    """
    return FXConfig(
        base_currency="USD",
        output_currency="USD",
        rates=DEFAULT_FX_RATES
    )

def load_fx_config(fx_config_path: Optional[str] = None) -> 'FXConfig':
    """
    Load FX configuration from a YAML file or return defaults.
    """
    default_config = get_default_fx_config()
    if fx_config_path is None:
        return default_config
    try:
        with open(fx_config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        if not isinstance(config, dict):
            raise ValueError("FX config must be a YAML mapping/object")

        # Validate schema/version (reject unknown/absent identifier).
        with open(FX_SCHEMA_PATH, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        validator = Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(config), key=lambda e: list(e.path))
        if errors:
            first = errors[0]
            path = " -> ".join(map(str, first.path)) if first.path else "(root)"
            raise ValueError(f"Invalid FX config: {first.message} at {path}")

        # Merge with defaults
        result = default_config.model_copy(deep=True)
        result.base_currency = config.get("base_currency", "USD")
        result.output_currency = config.get("output_currency", result.base_currency)

        if "rates" in config:
            result.rates = {**DEFAULT_FX_RATES, **(config.get("rates") or {})}
        result.as_of = config.get("as_of")

        # Ensure output_symbol stays consistent (older code used currency_symbol)
        result.output_symbol = get_currency_symbol(result.output_currency)
        return result
    except Exception as e:
        print(f"Warning: Could not load FX config from {fx_config_path}: {e}")
        default_config.output_symbol = get_currency_symbol(default_config.output_currency)
        return default_config

def get_currency_symbol(currency: str) -> str:
    """
    Get the display symbol for a currency code.
    If already a symbol or unknown code, returns the input unchanged.
    """
    return CURRENCY_CODE_TO_SYMBOL.get(currency.upper(), currency)

def convert_currency(amount: float, from_currency: str, to_currency: str, fx_config: Optional['FXConfig'] = None) -> float:
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
        fx_config = FXConfig(base_currency="USD", output_currency="USD", rates=DEFAULT_FX_RATES)
    rates = fx_config.rates
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

def normalize_currency(amount: float, from_currency: str, fx_context: Optional['FXConfig'] = None) -> float:
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
        fx_context = FXConfig(base_currency="USD", output_currency="USD", rates=DEFAULT_FX_RATES)
    base_currency = fx_context.base_currency
    rates = fx_context.rates
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

def normalize_fx_config(fx_config: Optional[dict or FXConfig]) -> FXConfig:
    """
    Normalize any FX config input (None, dict, FXConfig) to a valid FXConfig object.
    Ensures 'rates' is always present and a dict.
    """
    if fx_config is None:
        return FXConfig(base_currency="USD", output_currency="USD", rates=DEFAULT_FX_RATES)
    if isinstance(fx_config, FXConfig):
        # Ensure rates is not None
        if fx_config.rates is None:
            fx_config.rates = DEFAULT_FX_RATES
        return fx_config
    if isinstance(fx_config, dict):
        fx_config = dict(fx_config)  # copy
        if 'rates' not in fx_config or not isinstance(fx_config['rates'], dict):
            fx_config['rates'] = DEFAULT_FX_RATES
        return FXConfig(**fx_config)
    raise ValueError("fx_config must be None, dict, or FXConfig")