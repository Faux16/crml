from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import AliasChoices, BaseModel, Field, ConfigDict, field_validator

from .scenario_model import Meta
from .control_ref import ControlId
from .coverage_model import Coverage
from .numberish import parse_intish


class CriticalityIndex(BaseModel):
    type: Optional[str] = Field(None, description="Criticality index method identifier (tool/engine-defined).")
    inputs: Optional[Dict[str, str]] = Field(
        None, description="Optional mapping of input names to asset fields/values used by the index."
    )
    weights: Optional[Dict[str, float]] = Field(
        None, description="Optional weights applied to inputs when computing the criticality index."
    )
    transform: Optional[str] = Field(None, description="Optional post-transform applied to the computed index.")


class Asset(BaseModel):
    name: str = Field(..., description="Unique asset name within the portfolio.")
    cardinality: int = Field(
        ..., ge=1, description="Number of identical asset units represented by this asset entry (>= 1)."
    )
    criticality_index: Optional[CriticalityIndex] = Field(
        None, description="Optional criticality index configuration for this asset."
    )
    tags: Optional[List[str]] = Field(None, description="Optional list of tags for grouping/filtering assets.")

    @field_validator("cardinality", mode="before")
    @classmethod
    def _parse_cardinality(cls, v):
        return parse_intish(v)


PortfolioMethod = Literal["sum", "mixture", "choose_one", "max"]


class PortfolioConstraints(BaseModel):
    require_paths_exist: bool = Field(
        False, description="If true, referenced file paths must exist during validation."
    )
    validate_scenarios: bool = Field(
        True, description="If true, referenced scenario files are schema-validated during portfolio validation."
    )
    validate_relevance: bool = Field(
        False,
        description=(
            "If true, perform additional relevance checks between the portfolio organization context "
            "(meta.locale/meta.industries/meta.company_sizes/meta.regulatory_frameworks) and the referenced scenarios. "
            "Also validates that portfolio control id namespaces align with declared regulatory frameworks."
        ),
    )


class PortfolioSemantics(BaseModel):
    method: PortfolioMethod = Field(..., description="Aggregation semantics used to combine scenario losses.")
    constraints: PortfolioConstraints = Field(
        default_factory=PortfolioConstraints, description="Validation/runtime constraints for this portfolio."
    )


class ScenarioBinding(BaseModel):
    # Minimal binding surface: explicit list of portfolio asset names.
    # If a scenario is per-asset-unit, this defines its exposure set.
    applies_to_assets: Optional[List[str]] = Field(
        None,
        description=(
            "Optional explicit list of portfolio asset names this scenario applies to. "
            "Used for per-asset-unit scenarios to define the exposure set."
        ),
    )


class ScenarioRef(BaseModel):
    id: str = Field(..., description="Unique scenario id within the portfolio.")
    path: str = Field(..., description="Path to the referenced CRML scenario document.")
    weight: Optional[float] = Field(
        None, description="Optional weight used by some portfolio aggregation methods (model-specific)."
    )
    binding: ScenarioBinding = Field(
        default_factory=ScenarioBinding, description="Optional binding/exposure configuration for this scenario."
    )
    tags: Optional[List[str]] = Field(None, description="Optional list of tags for grouping/filtering scenarios.")


class CorrelationRelationship(BaseModel):
    type: Literal["correlation"] = Field(..., description="Relationship type discriminator.")
    between: List[str] = Field(
        ..., min_length=2, max_length=2, description="Pair of scenario ids this correlation applies to."
    )
    value: float = Field(..., ge=-1.0, le=1.0, description="Correlation coefficient in [-1, 1].")
    method: Optional[Literal["gaussian_copula", "rank_correlation"]] = Field(
        None, description="Optional correlation method used by the runtime (engine-defined)."
    )


class ConditionalRelationship(BaseModel):
    type: Literal["conditional"] = Field(..., description="Relationship type discriminator.")
    given: str = Field(..., description="Scenario id representing the condition event.")
    then: str = Field(..., description="Scenario id whose behavior depends on the condition event.")
    probability: float = Field(
        ..., ge=0.0, le=1.0, description="Conditional probability in [0, 1]."
    )


Relationship = CorrelationRelationship | ConditionalRelationship


class PortfolioControl(BaseModel):
    # Canonical unique control id, e.g. "cis.v8.2.3" or "iso27001:2022:A.5.1".
    id: ControlId = Field(..., description="Canonical unique control id present in the portfolio inventory.")
    implementation_effectiveness: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description=(
            "Portfolio-level implementation strength for this control (0..1). Represents organization-specific "
            "vulnerability likelihood (susceptibility) reduction when applied to a scenario's baseline threat frequency."
        ),
    )
    coverage: Optional[Coverage] = Field(
        None,
        description=(
            "Breadth of deployment/application across the organization. This contributes to vulnerability likelihood reduction "
            "when the control is used to mitigate a scenario's baseline threat frequency."
        ),
    )
    # Reliability/uptime of the control as a probability of being effective in a given period.
    # This is a portfolio/inventory attribute; runtimes may treat it as a stochastic state.
    reliability: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description=(
            "Reliability/uptime probability for this control being effective in a given period. "
            "This is an inventory attribute; runtimes may treat it as a stochastic state."
        ),
    )

    # Effect surface for this control. Default is frequency-first.
    affects: Optional[Literal["frequency", "severity", "both"]] = Field(
        "frequency",
        description=(
            "Which loss component this control is intended to affect (frequency, severity, or both). "
            "Note: the current reference engine primarily applies controls to frequency (lambda)."
        ),
    )
    notes: Optional[str] = Field(None, description="Free-form notes about this portfolio control entry.")


class DependencyCopula(BaseModel):
    """Engine-independent copula dependency specification.

    The copula operates over `targets` in the given order.
    This version is intentionally minimal and supports Gaussian copulas.

    Targets are language-level references. Currently supported targets:
    - control:<id>:state  (a control availability/performance state)
    """

    type: Literal["gaussian"] = Field("gaussian", description="Copula family/type discriminator.")

    # Ordered list of target references; length defines the copula dimension.
    targets: List[str] = Field(
        ...,
        min_length=1,
        description=(
            "Ordered list of dependency target references; list length defines the copula dimension."
        ),
    )

    # Correlation specification: either Toeplitz (rho) or an explicit matrix.
    structure: Optional[Literal["toeplitz"]] = Field(
        None, description="Optional shorthand correlation structure (e.g. toeplitz)."
    )
    rho: Optional[float] = Field(
        None,
        ge=-1.0,
        le=1.0,
        description="Toeplitz correlation parameter (used when structure='toeplitz').",
    )
    matrix: Optional[List[List[float]]] = Field(
        None, description="Optional explicit correlation matrix (dimension must match targets)."
    )


class PortfolioDependency(BaseModel):
    copula: Optional[DependencyCopula] = Field(
        None, description="Optional copula specification for dependency across targets."
    )


class Portfolio(BaseModel):
    assets: List[Asset] = Field(
        default_factory=list, description="List of assets/exposures in the portfolio."
    )
    controls: Optional[List[PortfolioControl]] = Field(
        None, description="Optional list of controls present in the organization/portfolio."
    )

    # Optional catalog references (paths). These allow portfolios to point at
    # portable catalogs/assessments without duplicating their contents.
    control_catalogs: Optional[List[str]] = Field(
        None, description="Optional list of file paths to referenced control catalogs."
    )

    attack_catalogs: Optional[List[str]] = Field(
        None,
        description=(
            "Optional list of file paths to referenced attack catalogs (e.g., MITRE ATT&CK). "
            "These are metadata-only catalogs used by tools/engines to resolve attack-pattern ids."
        ),
    )
    assessments: Optional[List[str]] = Field(
        None,
        validation_alias=AliasChoices("assessments", "control_assessments"),
        serialization_alias="assessments",
        description="Optional list of file paths to referenced assessment catalogs.",
    )

    control_relationships: Optional[List[str]] = Field(
        None,
        description=(
            "Optional list of file paths to referenced control relationships packs (control-to-control mappings). "
            "These can be used by tools/engines to resolve scenario control ids to implemented portfolio controls with quantitative overlap metadata."
        ),
    )

    attack_control_relationships: Optional[List[str]] = Field(
        None,
        description=(
            "Optional list of file paths to referenced attack-to-control relationships mappings. "
            "These can be used by tools/engines to translate attack-pattern ids (e.g., ATT&CK) into relevant controls."
        ),
    )

    scenarios: List[ScenarioRef] = Field(..., description="List of scenario references included in the portfolio.")
    semantics: PortfolioSemantics = Field(..., description="Portfolio aggregation semantics and constraints.")
    relationships: Optional[List[Relationship]] = Field(
        None, description="Optional relationships between scenarios (correlation/conditional)."
    )
    dependency: Optional[PortfolioDependency] = Field(
        None, description="Optional dependency specification for runtime models (e.g. copulas)."
    )
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Free-form context object for tools/runtimes (engine-defined).",
    )


class CRPortfolio(BaseModel):
    crml_portfolio: Literal["1.0"] = Field(..., description="Portfolio document version identifier.")
    meta: Meta = Field(..., description="Document metadata (name, description, tags, etc.).")
    portfolio: Portfolio = Field(..., description="The portfolio payload.")

    model_config: ConfigDict = ConfigDict(populate_by_name=True)
