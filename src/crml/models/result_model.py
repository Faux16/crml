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
    eal: Optional[float] = None
    var_95: Optional[float] = None
    var_99: Optional[float] = None
    var_999: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    median: Optional[float] = None
    std_dev: Optional[float] = None

class Distribution(BaseModel):
    bins: List[float] = Field(default_factory=list)
    frequencies: List[int] = Field(default_factory=list)
    raw_data: List[float] = Field(default_factory=list)

class Metadata(BaseModel):
    runs: int
    seed: Optional[int] = None
    currency: Optional[str] = None
    currency_code: Optional[str] = None
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    description: Optional[str] = None
    runtime_ms: Optional[float] = None
    lambda_baseline: Optional[float] = None
    lambda_effective: Optional[float] = None
    controls_applied: Optional[bool] = None
    control_reduction_pct: Optional[float] = None
    control_details: Optional[Any] = None
    control_warnings: Optional[Any] = None
    control_warning: Optional[str] = None

class SimulationResult(BaseModel):
    success: bool = False
    metrics: Optional[Metrics] = None
    distribution: Optional[Distribution] = None
    metadata: Optional[Metadata] = None
    errors: List[str] = Field(default_factory=list)

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