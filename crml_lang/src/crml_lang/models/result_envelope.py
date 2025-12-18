from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class CurrencyUnit(BaseModel):
    kind: Literal["currency"] = Field("currency", description="Unit kind discriminator.")
    code: str = Field(..., description="ISO 4217 currency code (e.g. 'USD', 'EUR').")
    symbol: Optional[str] = Field(None, description="Optional currency display symbol (e.g. '$', '€').")


class Units(BaseModel):
    currency: CurrencyUnit = Field(..., description="Currency unit used for monetary measures/artifacts.")
    horizon: Optional[Literal["annual", "monthly", "daily", "event", "unknown"]] = Field(
        "unknown",
        description="Time horizon/period unit for rates/annualized figures when applicable.",
    )


class EngineInfo(BaseModel):
    name: str = Field(..., description="Engine name/identifier.")
    version: Optional[str] = Field(None, description="Engine version string.")


class RunInfo(BaseModel):
    runs: Optional[int] = Field(None, description="Number of Monte Carlo runs/samples executed.")
    seed: Optional[int] = Field(None, description="Random seed used by the engine (if any).")
    runtime_ms: Optional[float] = Field(None, description="Execution time in milliseconds (best-effort).")
    started_at: Optional[datetime] = Field(None, description="UTC timestamp when execution started.")


class InputInfo(BaseModel):
    model_name: Optional[str] = Field(None, description="Optional input model name (from scenario/portfolio meta).")
    model_version: Optional[str] = Field(None, description="Optional input model version (from scenario/portfolio meta).")
    description: Optional[str] = Field(None, description="Optional input model description (from meta).")


class Measure(BaseModel):
    id: str = Field(..., description="Measure identifier (e.g. 'eal', 'var_95').")
    value: Optional[float] = Field(None, description="Numeric measure value.")
    unit: Optional[CurrencyUnit] = Field(None, description="Optional unit metadata for this measure.")
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional parameterization metadata for this measure (engine/UI defined).",
    )
    label: Optional[str] = Field(None, description="Optional human-friendly label for display.")


class HistogramArtifact(BaseModel):
    kind: Literal["histogram"] = Field("histogram", description="Artifact kind discriminator.")
    id: str = Field(..., description="Artifact identifier.")
    unit: Optional[CurrencyUnit] = Field(None, description="Optional unit metadata for this artifact.")
    bin_edges: List[float] = Field(default_factory=list, description="Histogram bin edge values.")
    counts: List[int] = Field(default_factory=list, description="Histogram bin counts (same length as bins minus one).")
    binning: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional binning configuration/metadata (engine-defined).",
    )


class SamplesArtifact(BaseModel):
    kind: Literal["samples"] = Field("samples", description="Artifact kind discriminator.")
    id: str = Field(..., description="Artifact identifier.")
    unit: Optional[CurrencyUnit] = Field(None, description="Optional unit metadata for this artifact.")
    values: List[float] = Field(default_factory=list, description="Sample values (may be truncated for size).")
    sample_count_total: Optional[int] = Field(None, description="Total sample count produced by the engine.")
    sample_count_returned: Optional[int] = Field(None, description="Number of samples included in 'values'.")
    sampling: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional sampling configuration/metadata (engine-defined).",
    )


Artifact = HistogramArtifact | SamplesArtifact


class ResultPayload(BaseModel):
    measures: List[Measure] = Field(default_factory=list, description="List of computed summary measures.")
    artifacts: List[Artifact] = Field(default_factory=list, description="List of computed artifacts (histograms/samples).")


class SimulationResult(BaseModel):
    """Simulation result payload for `SimulationResultEnvelope`."""

    success: bool = Field(False, description="True if the run completed successfully.")
    errors: List[str] = Field(default_factory=list, description="List of error messages (if any).")
    warnings: List[str] = Field(default_factory=list, description="List of warning messages (if any).")

    engine: EngineInfo = Field(..., description="Engine identification and version metadata.")
    run: RunInfo = Field(default_factory=RunInfo, description="Execution/run metadata.")
    inputs: InputInfo = Field(default_factory=InputInfo, description="Input model metadata captured for reporting.")
    units: Optional[Units] = Field(None, description="Optional unit metadata for values in this result.")

    results: ResultPayload = Field(default_factory=ResultPayload, description="The result payload (measures/artifacts).")


class SimulationResultEnvelope(BaseModel):
    """Engine-agnostic, visualization-agnostic simulation result envelope.

    This model lives in `crml_lang` so engines and UIs can share a stable contract.
    """

    crml_simulation_result: Literal["1.0"] = Field(
        "1.0",
        description="Simulation result document version identifier.",
    )

    result: SimulationResult = Field(..., description="The simulation result payload.")


def now_utc() -> datetime:
    """Return the current UTC timestamp (timezone-aware)."""
    return datetime.now(timezone.utc)
