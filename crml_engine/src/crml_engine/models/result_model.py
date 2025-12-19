# This module defines the Pydantic models used to represent the results of CRML simulations.
#
# Main Models:
#   - SimulationResult: The top-level result object, containing success status, metrics, distribution, metadata, and errors.
#   - Metrics: Statistical outputs such as EAL, VaR, min, max, median, and standard deviation.
#   - Distribution: Histogram data for loss distributions (bins, frequencies, raw data).
#   - Metadata: Simulation context (run count, currency, model name/version, runtime, control info, etc.).
#
# Purpose:
#   - Provides a type-safe, attribute-accessible structure for all simulation outputs.
#   - Ensures consistency and validation of result data across the codebase.
#   - Used by runtime.py
#
# Usage:
#   - Import and use these models to construct, validate, or serialize simulation results.
#   - Enables easy conversion to JSON or dict via Pydantic's .model_dump()/.dict() methods.
#
# Example:
#   result = SimulationResult(success=True, metrics=Metrics(eal=123.4, ...), ...)
#   print(result.metrics.eal)
#   print(result.model_dump())
from typing import Optional, List, Any

from pydantic import BaseModel, Field


_BANNER_WIDTH = 50

class Metrics(BaseModel):
    eal: Optional[float] = Field(None, description="Expected annual loss (mean of the annual loss distribution).")
    var_95: Optional[float] = Field(None, description="Value at Risk at the 95th percentile.")
    var_99: Optional[float] = Field(None, description="Value at Risk at the 99th percentile.")
    var_999: Optional[float] = Field(None, description="Value at Risk at the 99.9th percentile.")
    min: Optional[float] = Field(None, description="Minimum observed/estimated loss.")
    max: Optional[float] = Field(None, description="Maximum observed/estimated loss.")
    median: Optional[float] = Field(None, description="Median of the loss distribution.")
    std_dev: Optional[float] = Field(None, description="Standard deviation of the loss distribution.")

class Distribution(BaseModel):
    bins: List[float] = Field(default_factory=list, description="Histogram bin edges.")
    frequencies: List[int] = Field(default_factory=list, description="Histogram bin counts.")
    raw_data: List[float] = Field(default_factory=list, description="Optional raw sample losses (may be truncated).")

class Metadata(BaseModel):
    runs: int = Field(..., description="Number of simulation runs/samples.")
    seed: Optional[int] = Field(None, description="Random seed used for the run (if any).")
    currency: Optional[str] = Field(None, description="Currency display symbol (if available).")
    currency_code: Optional[str] = Field(None, description="ISO 4217 currency code (if available).")
    model_name: Optional[str] = Field(None, description="Input model name (from meta).")
    model_version: Optional[str] = Field(None, description="Input model version (from meta).")
    description: Optional[str] = Field(None, description="Input model description (from meta).")
    runtime_ms: Optional[float] = Field(None, description="Runtime duration in milliseconds.")
    lambda_baseline: Optional[float] = Field(None, description="Baseline frequency rate (engine-specific).")
    lambda_effective: Optional[float] = Field(None, description="Effective frequency rate after modifiers/controls (engine-specific).")
    controls_applied: Optional[bool] = Field(None, description="Whether any controls were applied in the run.")
    control_reduction_pct: Optional[float] = Field(None, description="Percent reduction due to controls (engine-specific).")
    control_details: Optional[Any] = Field(None, description="Optional structured control details (engine-specific).")
    control_warnings: Optional[Any] = Field(None, description="Optional structured control warnings (engine-specific).")
    correlation_info: Optional[List[dict]] = Field(None, description="Optional correlation metadata (engine-specific).")

class SimulationResult(BaseModel):
    success: bool = Field(False, description="True if simulation completed successfully.")
    metrics: Optional[Metrics] = Field(None, description="Computed summary statistics for the run.")
    distribution: Optional[Distribution] = Field(None, description="Distribution artifacts for loss samples.")
    metadata: Optional[Metadata] = Field(None, description="Run metadata and context.")
    errors: List[str] = Field(default_factory=list, description="List of error messages (if any).")

def _banner(title: str) -> None:
    """Print a section banner used by `print_result()`."""
    line = "=" * _BANNER_WIDTH
    print("\n" + line)
    print(title)
    print(line)


def _currency_display(meta: Optional[Metadata]) -> tuple[str, str]:
    """Resolve display currency symbol and code from metadata.

    Args:
        meta: Optional metadata.

    Returns:
        (symbol, code) falling back to ($, USD) if not specified.
    """
    symbol = meta.currency if (meta and meta.currency) else "$"
    code = meta.currency_code if (meta and meta.currency_code) else "USD"
    return symbol, code


def _print_failure(errors: List[str]) -> None:
    """Print a formatted failure header and list of error messages."""
    print("❌ Simulation failed:")
    for error in errors:
        print(f"  • {error}")


def _print_metadata(meta: Optional[Metadata], *, currency_symbol: str, currency_code: str) -> None:
    """Print metadata fields for a successful simulation run."""
    model_name = meta.model_name if (meta and meta.model_name) else ""
    print(f"Model: {model_name}")

    if meta and meta.runs:
        print(f"Runs: {meta.runs:,}")
    if meta and meta.runtime_ms is not None:
        print(f"Runtime: {meta.runtime_ms:.2f} ms")
    if meta and meta.seed:
        print(f"Seed: {meta.seed}")

    print(f"Currency: {currency_code} ({currency_symbol})")


def _print_metrics(metrics: Optional[Metrics], *, currency_symbol: str) -> None:
    """Print metrics for a successful simulation run."""
    if not metrics:
        return

    if metrics.eal is not None:
        print(f"EAL (Expected Annual Loss):  {currency_symbol}{metrics.eal:,.2f}")
    if metrics.var_95 is not None:
        print(f"VaR 95%:                      {currency_symbol}{metrics.var_95:,.2f}")
    if metrics.var_99 is not None:
        print(f"VaR 99%:                      {currency_symbol}{metrics.var_99:,.2f}")
    if metrics.var_999 is not None:
        print(f"VaR 99.9%:                    {currency_symbol}{metrics.var_999:,.2f}")

    if any(v is not None for v in (metrics.min, metrics.max, metrics.median, metrics.std_dev)):
        print("")
    if metrics.min is not None:
        print(f"Min Loss:                     {currency_symbol}{metrics.min:,.2f}")
    if metrics.max is not None:
        print(f"Max Loss:                     {currency_symbol}{metrics.max:,.2f}")
    if metrics.median is not None:
        print(f"Median Loss:                  {currency_symbol}{metrics.median:,.2f}")
    if metrics.std_dev is not None:
        print(f"Std Deviation:                {currency_symbol}{metrics.std_dev:,.2f}")


def print_result(result: "SimulationResult") -> None:
    """Pretty-print a `SimulationResult` object to the console.

    This is intended for CLI usage and human inspection.

    Args:
        result: Simulation result to render.

    Side effects:
        Writes to stdout.
    """

    if not result.success:
        _print_failure(result.errors)
        return

    meta = result.metadata
    metrics = result.metrics
    curr_symbol, curr_code = _currency_display(meta)

    _banner("CRML Simulation Results")
    _print_metadata(meta, currency_symbol=curr_symbol, currency_code=curr_code)

    _banner("Risk Metrics")
    _print_metrics(metrics, currency_symbol=curr_symbol)

    print("=" * _BANNER_WIDTH + "\n")