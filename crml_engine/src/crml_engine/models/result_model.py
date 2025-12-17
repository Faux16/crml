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
    control_warning: Optional[str] = Field(None, description="Optional single warning string (legacy/compat).")
    correlation_info: Optional[List[dict]] = Field(None, description="Optional correlation metadata (engine-specific).")

class SimulationResult(BaseModel):
    success: bool = Field(False, description="True if simulation completed successfully.")
    metrics: Optional[Metrics] = Field(None, description="Computed summary statistics for the run.")
    distribution: Optional[Distribution] = Field(None, description="Distribution artifacts for loss samples.")
    metadata: Optional[Metadata] = Field(None, description="Run metadata and context.")
    errors: List[str] = Field(default_factory=list, description="List of error messages (if any).")

def print_result(result: 'SimulationResult'):
    """
    Pretty-print a SimulationResult object to the console.
    """
    if not result.success:
        print("❌ Simulation failed:")
        for error in result.errors:
            print(f"  • {error}")
        return
    meta = result.metadata
    metrics = result.metrics
    curr = meta.currency or '$' if meta else '$'
    curr_code = meta.currency_code or 'USD' if meta else 'USD'
    print(f"\n{'='*50}")
    print(f"CRML Simulation Results")
    print(f"{'='*50}")
    print(f"Model: {meta.model_name if meta else ''}")
    print(f"Runs: {meta.runs:,}" if meta and meta.runs else "")
    print(f"Runtime: {meta.runtime_ms:.2f} ms" if meta and meta.runtime_ms else "")
    if meta and meta.seed:
        print(f"Seed: {meta.seed}")
    print(f"Currency: {curr_code} ({curr})")
    print(f"\n{'='*50}")
    print(f"Risk Metrics")
    print(f"{'='*50}")
    if metrics:
        print(f"EAL (Expected Annual Loss):  {curr}{metrics.eal:,.2f}" if metrics.eal is not None else "")
        print(f"VaR 95%:                      {curr}{metrics.var_95:,.2f}" if metrics.var_95 is not None else "")
        print(f"VaR 99%:                      {curr}{metrics.var_99:,.2f}" if metrics.var_99 is not None else "")
        print(f"VaR 99.9%:                    {curr}{metrics.var_999:,.2f}" if metrics.var_999 is not None else "")
        print(f"\nMin Loss:                     {curr}{metrics.min:,.2f}" if metrics.min is not None else "")
        print(f"Max Loss:                     {curr}{metrics.max:,.2f}" if metrics.max is not None else "")
        print(f"Median Loss:                  {curr}{metrics.median:,.2f}" if metrics.median is not None else "")
        print(f"Std Deviation:                {curr}{metrics.std_dev:,.2f}" if metrics.std_dev is not None else "")
    print(f"{'='*50}\n")