from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from ..yamlio import (
    dump_yaml_to_path,
    dump_yaml_to_str,
    load_yaml_mapping_from_path,
    load_yaml_mapping_from_str,
)


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


class Quantile(BaseModel):
    p: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Quantile probability level in [0,1]. Example: 0.95 for P95.",
    )
    value: Optional[float] = Field(None, description="Quantile value at probability level `p`.")


class TailExpectation(BaseModel):
    kind: Literal["cvar", "expected_shortfall"] = Field(
        "cvar",
        description="Tail expectation kind. 'cvar' is synonymous with Expected Shortfall in many contexts.",
    )
    level: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence level for the tail expectation in [0,1]. Example: 0.95.",
    )
    tail: Literal["right", "left"] = Field(
        "right",
        description="Which tail is considered extreme. For losses, this is typically the right tail.",
    )
    value: Optional[float] = Field(None, description="Tail expectation value at the given level.")


class SummaryEstimation(BaseModel):
    computed_from: Optional[Literal["samples", "histogram", "analytic", "hybrid", "unknown"]] = Field(
        "unknown",
        description="How the summary statistics were computed (engine-defined).",
    )
    sample_count_used: Optional[int] = Field(
        None,
        description="Number of samples used to compute summary statistics (if applicable).",
    )
    histogram_bins_used: Optional[int] = Field(
        None,
        description="Number of histogram bins used to compute summary statistics (if applicable).",
    )
    truncated: Optional[bool] = Field(
        None,
        description="Whether the underlying samples/histogram used for summary statistics were truncated.",
    )
    method: Optional[str] = Field(
        None,
        description="Optional method notes (e.g., quantile algorithm, KDE bandwidth), engine-defined.",
    )


class SummaryStatistics(BaseModel):
    mean: Optional[float] = Field(None, description="Mean of the target distribution.")
    median: Optional[float] = Field(None, description="Median (P50) of the target distribution.")
    mode: Optional[float] = Field(
        None,
        description="Mode of the target distribution if well-defined/estimated (engine-defined).",
    )
    std_dev: Optional[float] = Field(None, description="Standard deviation of the target distribution.")
    quantiles: List[Quantile] = Field(
        default_factory=list,
        description="Requested/available quantiles (e.g., P5/P50/P90/P95/P99) as probability/value pairs.",
    )
    tail_expectations: List[TailExpectation] = Field(
        default_factory=list,
        description="Tail expectation measures such as CVaR/Expected Shortfall.",
    )


class SummaryBlock(BaseModel):
    id: str = Field(
        ...,
        description=(
            "Identifier for the summarized target distribution. "
            "Should align with a measure/artifact id where possible (e.g., 'loss.annual')."
        ),
    )
    label: Optional[str] = Field(None, description="Optional human-friendly label for the target distribution.")
    unit: Optional[CurrencyUnit] = Field(
        None,
        description="Optional unit metadata for all values in this summary block.",
    )
    stats: SummaryStatistics = Field(
        default_factory=SummaryStatistics,
        description="Computed summary statistics for this target distribution.",
    )
    estimation: SummaryEstimation = Field(
        default_factory=SummaryEstimation,
        description="Optional metadata describing how the statistics were computed.",
    )


class InputReference(BaseModel):
    type: str = Field(
        ...,
        description=(
            "Input document type identifier (engine/UI defined). Examples: 'scenario', 'portfolio', 'bundle', 'fx_config'."
        ),
    )
    id: Optional[str] = Field(
        None,
        description="Optional stable identifier for the input (scenario id, portfolio scenario id, document id, etc.).",
    )
    version: Optional[str] = Field(None, description="Optional input document version or revision identifier.")
    uri: Optional[str] = Field(
        None,
        description="Optional URI or path reference used to load the input (if applicable).",
    )
    digest: Optional[str] = Field(
        None,
        description=(
            "Optional integrity digest for the loaded input (e.g., 'sha256:<hex>'). "
            "Useful for auditability without embedding full documents."
        ),
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional additional input metadata (engine-defined).",
    )


class ModelComponent(BaseModel):
    id: str = Field(..., description="Unique identifier for this model component within the run trace.")
    role: Optional[str] = Field(
        None,
        description=(
            "Component role/category (engine-defined). Examples: 'frequency', 'severity', 'exposure', 'control', 'dependency', 'prior', 'likelihood'."
        ),
    )
    model: Optional[str] = Field(
        None,
        description=(
            "Distribution/model identifier (engine-defined). Examples: 'poisson', 'lognormal', 'bayesian_network', 'mcmc'."
        ),
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Resolved parameter values for this component (engine-defined, should be JSON/YAML-serializable).",
    )
    units: Optional[Units] = Field(
        None,
        description="Optional unit metadata relevant to this component (if any).",
    )
    source_input_id: Optional[str] = Field(
        None,
        description="Optional reference to an InputReference.id indicating where this component came from.",
    )
    notes: Optional[str] = Field(None, description="Optional free-form notes for audit/review (engine-defined).")


class DependencyStructure(BaseModel):
    kind: str = Field(
        ...,
        description=(
            "Dependency structure kind (engine-defined). Examples: 'correlation_matrix', 'copula', 'bayesian_network', 'graph'."
        ),
    )
    targets: List[str] = Field(
        default_factory=list,
        description="List of component ids this dependency structure applies to.",
    )
    structure: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structural definition (e.g., matrix, graph edges), engine-defined.",
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional dependency parameters (e.g., copula family), engine-defined.",
    )


class Traceability(BaseModel):
    scenario_ids: List[str] = Field(
        default_factory=list,
        description=(
            "Scenario identifiers in effect for this run (if applicable). "
            "For portfolios/bundles, this may include portfolio-local scenario ids."
        ),
    )
    inputs: List[InputReference] = Field(
        default_factory=list,
        description="References and integrity metadata for input documents used in the run.",
    )
    model_components: List[ModelComponent] = Field(
        default_factory=list,
        description="Resolved model components used by the engine (distributions, priors, controls, etc.).",
    )
    dependencies: List[DependencyStructure] = Field(
        default_factory=list,
        description="Dependency/coupling structures used by the run (copulas, correlations, graphs, etc.).",
    )
    extra: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional additional trace/provenance details (engine-defined).",
    )


class ResultPayload(BaseModel):
    measures: List[Measure] = Field(default_factory=list, description="List of computed summary measures.")
    artifacts: List[Artifact] = Field(default_factory=list, description="List of computed artifacts (histograms/samples).")


class SimulationResult(BaseModel):
    """Simulation result payload for `CRSimulationResult`."""

    success: bool = Field(False, description="True if the run completed successfully.")
    errors: List[str] = Field(default_factory=list, description="List of error messages (if any).")
    warnings: List[str] = Field(default_factory=list, description="List of warning messages (if any).")

    engine: EngineInfo = Field(..., description="Engine identification and version metadata.")
    run: RunInfo = Field(default_factory=RunInfo, description="Execution/run metadata.")
    inputs: InputInfo = Field(default_factory=InputInfo, description="Input model metadata captured for reporting.")
    units: Optional[Units] = Field(None, description="Optional unit metadata for values in this result.")

    summaries: List[SummaryBlock] = Field(
        default_factory=list,
        description=(
            "Optional summary-statistics blocks for one or more target distributions. "
            "This provides a stable place for common analyst-facing statistics like P5/P50/P90/P95/P99, mean, std dev, and tail expectations."
        ),
    )

    trace: Optional[Traceability] = Field(
        None,
        description=(
            "Optional traceability/provenance block capturing resolved inputs, distributions/parameters, and dependency structures for auditability."
        ),
    )

    results: ResultPayload = Field(default_factory=ResultPayload, description="The result payload (measures/artifacts).")


class CRSimulationResult(BaseModel):
    """Engine-agnostic, visualization-agnostic simulation result document.

    This model lives in `crml_lang` so engines and UIs can share a stable contract.
    """

    crml_simulation_result: Literal["1.0"] = Field(
        "1.0",
        description="Simulation result document version identifier.",
    )

    result: SimulationResult = Field(..., description="The simulation result payload.")

    @classmethod
    def load_from_yaml(cls, path: str) -> "CRSimulationResult":
        """Load a simulation result envelope from a YAML file path."""

        data = load_yaml_mapping_from_path(path)
        return cls.model_validate(data)

    @classmethod
    def load_from_yaml_str(cls, yaml_text: str) -> "CRSimulationResult":
        """Load a simulation result envelope from a YAML string."""

        data = load_yaml_mapping_from_str(yaml_text)
        return cls.model_validate(data)

    def dump_to_yaml(self, path: str, *, sort_keys: bool = False, exclude_none: bool = True) -> None:
        """Serialize this envelope to a YAML file at `path`."""

        data = self.model_dump(by_alias=True, exclude_none=exclude_none)
        dump_yaml_to_path(data, path, sort_keys=sort_keys)

    def dump_to_yaml_str(self, *, sort_keys: bool = False, exclude_none: bool = True) -> str:
        """Serialize this envelope to a YAML string."""

        data = self.model_dump(by_alias=True, exclude_none=exclude_none)
        return dump_yaml_to_str(data, sort_keys=sort_keys)


def now_utc() -> datetime:
    """Return the current UTC timestamp (timezone-aware)."""
    return datetime.now(timezone.utc)
