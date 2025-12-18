"""scenario_model.py

Scenario-first CRML language models.

This module defines the CRML *Scenario* document.

Key design rule:
- A scenario is validated and exchanged on its own, but it is only *executable*
    within a CRML Portfolio (which provides assets/exposure and scenario relations).

Consequences:
- Assets (inventory/exposure) are NOT part of the scenario document.
- Portfolio-level concerns (aggregation, correlations across scenarios, etc.) are
    defined in a separate portfolio schema/model.
"""

from typing import Annotated, Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .numberish import parse_floatish, parse_float_list
from .control_ref import ControlId
from .coverage_model import Coverage


AttckId = Annotated[
    str,
    Field(
        min_length=1,
        max_length=256,
        pattern=r"^[a-z][a-z0-9_-]{0,31}:[^\s]{1,223}$",
        description=(
            "ATT&CK identifier in canonical namespaced form 'namespace:key' (no whitespace). "
            "Recommended namespace is 'attck'. Examples: attck:TA0001, attck:T1059, attck:T1059.003"
        ),
    ),
]


# --- $defs ---
class ISO3166Alpha2(str):
    pass


# --- Meta ---
class Meta(BaseModel):
    name: str = Field(..., description="Human-friendly name for this document.")
    version: Optional[str] = Field(None, description="Optional version string for this document.")
    description: Optional[str] = Field(None, description="Optional free-form description.")
    author: Optional[str] = Field(None, description="Optional author/owner.")
    organization: Optional[str] = Field(None, description="Optional organization name.")
    industries: Optional[List[str]] = Field(None, description="Optional list of industry tags.")
    locale: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional locale/region information and arbitrary locale metadata.",
    )
    company_sizes: Optional[List[str]] = Field(None, description="Optional company size tags.")
    regulatory_frameworks: Optional[List[str]] = Field(
        None, description="Optional list of regulatory frameworks relevant to this document."
    )
    tags: Optional[List[str]] = Field(None, description="Optional list of user-defined tags.")

    attck: Optional[List[AttckId]] = Field(
        None,
        description=(
            "Optional list of ATT&CK tactic/technique/sub-technique identifiers relevant to this document, "
            "expressed as namespaced ids (e.g. 'attck:T1059.003')."
        ),
    )


# --- Data ---
class DataSource(BaseModel):
    type: str = Field(..., description="Identifier for the data source type (engine/UI defined).")
    data_schema: Optional[Dict[str, str]] = Field(
        None,
        description="Optional schema mapping for source fields (feature name -> type/meaning).",
    )


class Data(BaseModel):
    sources: Optional[Dict[str, DataSource]] = Field(
        None, description="Optional named data sources referenced by the scenario."
    )
    feature_mapping: Optional[Dict[str, str]] = Field(
        None, description="Optional mapping from engine-required feature names to source columns/fields."
    )


# --- Evidence (citations + lightweight observed metrics) ---
class EvidenceSource(BaseModel):
    title: Optional[str] = Field(None, description="Optional title of the source (report/article).")
    publisher: Optional[str] = Field(None, description="Optional publisher/vendor name.")
    url: Optional[str] = Field(None, description="Optional URL for the source.")
    published_at: Optional[str] = Field(
        None,
        description=(
            "Optional publish timestamp/date for the source (ISO 8601 string). "
            "Examples: '2025-12-01' or '2025-12-01T10:15:30Z'."
        ),
    )
    retrieved_at: Optional[str] = Field(
        None,
        description=(
            "Optional retrieval timestamp/date (ISO 8601 string). "
            "Useful for threat intel that changes over time."
        ),
    )
    notes: Optional[str] = Field(None, description="Optional notes about how this source was used.")


class EvidenceWindow(BaseModel):
    start: Optional[str] = Field(
        None,
        description=(
            "Optional start of the observation window (ISO 8601 string). "
            "Example: '2023-01-01'."
        ),
    )
    end: Optional[str] = Field(
        None,
        description=(
            "Optional end of the observation window (ISO 8601 string). "
            "Example: '2025-12-31'."
        ),
    )


class EvidenceObserved(BaseModel):
    window: Optional[EvidenceWindow] = Field(
        None, description="Optional time window for the observations used to inform this scenario."
    )
    incident_count: Optional[int] = Field(
        None,
        ge=0,
        description=(
            "Optional observed incident count for this scenario within the window. "
            "Useful for calibrating frequency."
        ),
    )
    org_count: Optional[int] = Field(
        None,
        ge=0,
        description=(
            "Optional number of organizations covered by the observations (if known). "
            "Useful for translating report-level counts into per-organization rates."
        ),
    )
    currency: Optional[str] = Field(None, description="Optional currency code/symbol for observed loss values.")
    loss_median: Optional[float] = Field(None, description="Optional observed median loss per incident.")
    loss_mean: Optional[float] = Field(None, description="Optional observed mean loss per incident.")
    loss_p90: Optional[float] = Field(None, description="Optional observed 90th percentile loss per incident.")
    loss_min: Optional[float] = Field(None, description="Optional observed minimum loss per incident.")
    loss_max: Optional[float] = Field(None, description="Optional observed maximum loss per incident.")

    @field_validator(
        "loss_median",
        "loss_mean",
        "loss_p90",
        "loss_min",
        "loss_max",
        mode="before",
    )
    @classmethod
    def _parse_losses(cls, v):
        if v is None:
            return None
        return parse_floatish(v, allow_percent=False)


class Evidence(BaseModel):
    sources: Optional[List[EvidenceSource]] = Field(
        None,
        description=(
            "Optional list of citations that informed this scenario (threat reports, news, internal docs). "
            "This is designed to support low-friction authoring from external reporting."
        ),
    )
    observed: Optional[EvidenceObserved] = Field(
        None,
        description=(
            "Optional lightweight observed metrics used to inform or calibrate the scenario. "
            "Tools may translate these into model parameters (e.g., lambda, median/sigma)."
        ),
    )
    notes: Optional[str] = Field(None, description="Optional evidence/provenance notes.")


# --- Model: Frequency ---
FrequencyBasis = Literal["per_organization_per_year", "per_asset_unit_per_year"]

# Constant for repeated frequency parameter description
FREQUENCY_PARAM_DESC = "Frequency model parameter (model-specific)."


class FrequencyParameters(BaseModel):
    lambda_: Optional[float] = Field(
        None,
        alias="lambda",
        description=(
            "Threat-event frequency parameter (e.g. Poisson rate). Interpreted as baseline "
            "threat likelihood (threat landscape) before organization-specific vulnerability/control posture "
            "is applied. Serialized as 'lambda' in YAML/JSON."
        ),
    )
    alpha_base: Optional[float] = Field(None, description=FREQUENCY_PARAM_DESC)
    beta_base: Optional[float] = Field(None, description=FREQUENCY_PARAM_DESC)
    r: Optional[float] = Field(None, description=FREQUENCY_PARAM_DESC)
    p: Optional[float] = Field(None, description="Probability parameter for frequency model (0..1).")

    @field_validator("lambda_", "alpha_base", "beta_base", "r", mode="before")
    @classmethod
    def _parse_numbers_no_percent(cls, v):
        if v is None:
            return None
        return parse_floatish(v, allow_percent=False)

    @field_validator("p", mode="before")
    @classmethod
    def _parse_probability(cls, v):
        if v is None:
            return None
        return parse_floatish(v, allow_percent=True)


class Frequency(BaseModel):
    basis: FrequencyBasis = Field(
        "per_organization_per_year",
        description="Frequency basis/denominator (e.g. per-organization-year, per-asset-unit-year).",
    )
    model: str = Field(
        "poisson",
        description=(
            "Frequency distribution/model identifier (engine-defined). "
            "If omitted, defaults to 'poisson'."
        ),
    )
    parameters: FrequencyParameters = Field(..., description="Model parameters for the selected frequency model.")


# --- Model: Severity ---
# Constant for repeated description
DISTRIBUTION_PARAM_DESC = "Distribution parameter (model-specific)."


class SeverityParameters(BaseModel):
    median: Optional[float] = Field(
        None,
        description=(
            "Median loss value (distribution-dependent). Interpreted as threat impact (monetary loss per event). "
            "The reference approach models vulnerability primarily via likelihood (controls); vulnerability impact is not modeled."
        ),
    )
    currency: Optional[str] = Field(None, description="Optional currency code/symbol for severity inputs.")
    mu: Optional[float] = Field(
        None,
        description=(
            "Distribution parameter (e.g. lognormal mu). Used to parameterize threat impact. "
            "Prefer 'median' for human-readable inputs."
        ),
    )
    sigma: Optional[float] = Field(
        None,
        description=(
            "Distribution parameter (e.g. lognormal sigma). Controls variability of threat impact (loss per event)."
        ),
    )
    shape: Optional[float] = Field(None, description=DISTRIBUTION_PARAM_DESC)
    scale: Optional[float] = Field(None, description=DISTRIBUTION_PARAM_DESC)
    alpha: Optional[float] = Field(None, description=DISTRIBUTION_PARAM_DESC)
    x_min: Optional[float] = Field(None, description="Minimum loss / truncation parameter (model-specific).")
    single_losses: Optional[List[float]] = Field(
        None,
        description="Optional list of explicit sample losses (used by some empirical severity models).",
    )

    @field_validator("median", "sigma", "shape", "scale", "alpha", "x_min", mode="before")
    @classmethod
    def _parse_numbers_no_percent(cls, v):
        if v is None:
            return None
        return parse_floatish(v, allow_percent=False)

    @field_validator("single_losses", mode="before")
    @classmethod
    def _parse_single_losses(cls, v):
        if isinstance(v, list):
            return parse_float_list(v, allow_percent=False)
        return v


class Severity(BaseModel):
    model: str = Field(..., description="Severity distribution/model identifier (engine-defined).")
    parameters: SeverityParameters = Field(..., description="Model parameters for the selected severity model.")
    components: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Optional component breakdown (engine/tool-defined structure).",
    )


class ScenarioControl(BaseModel):
    """Scenario-specific control reference.

    This allows a scenario to specify scenario-scoped assumptions for a control
    (e.g. partial applicability) without requiring portfolio-wide changes.
    """

    id: ControlId = Field(..., description="Canonical unique control id referenced by this scenario.")
    effectiveness_against_threat: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description=(
            "Threat-specific effectiveness factor for this control against this scenario (0..1). "
            "Recommended semantics: engines combine this with organization-specific inventory/assessment posture (e.g. "
            "inventory implementation effectiveness and coverage) when planning."
        ),
    )
    notes: Optional[str] = Field(None, description="Free-form notes about this scenario control reference.")


class Scenario(BaseModel):
    frequency: Frequency = Field(..., description="Frequency model definition.")
    severity: Severity = Field(..., description="Severity model definition.")
    # Threat-centric declaration of relevant controls.
    # Semantics: "This threat can be mitigated by these controls (if present in the portfolio)".
    controls: Optional[List[Union[ControlId, ScenarioControl]]] = Field(
        None,
        description=(
            "Optional threat-centric declaration of relevant controls. "
            "Semantics: the threat can be mitigated by these controls if present in the portfolio."
        ),
    )


# --- Root CRML Scenario Schema ---
class CRScenarioSchema(BaseModel):
    # Scenario document version.
    crml_scenario: Literal["1.0"] = Field(..., description="Scenario document version identifier.")
    meta: Meta = Field(..., description="Document metadata (name, description, tags, etc.).")
    evidence: Optional[Evidence] = Field(
        None,
        description=(
            "Optional evidence/provenance section designed for scenarios authored from threat reports/news "
            "and for lightweight calibration metadata."
        ),
    )
    data: Optional[Data] = Field(None, description="Optional data source and feature mapping section.")
    scenario: Scenario = Field(..., description="The scenario payload.")

    # Pydantic v2 config
    model_config: ConfigDict = ConfigDict(populate_by_name=True, extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def _forbid_model_payload(cls, v):
        if isinstance(v, dict) and "model" in v:
            raise ValueError("Scenario documents must use 'scenario:' (top-level 'model:' is not allowed).")
        return v


# Usage: CRScenarioSchema.model_validate(your_json_dict)


def load_crml_from_yaml(path: str) -> CRScenarioSchema:
    """Load a CRML Scenario YAML file from `path` and validate it.

    Requires PyYAML (`pip install pyyaml`).
    """

    from ..yamlio import load_yaml_mapping_from_path

    data = load_yaml_mapping_from_path(path)

    return CRScenarioSchema.model_validate(data)


def load_crml_from_yaml_str(yaml_text: str) -> CRScenarioSchema:
    """Load a CRML Scenario document from a YAML string and validate."""

    from ..yamlio import load_yaml_mapping_from_str

    data = load_yaml_mapping_from_str(yaml_text)
    return CRScenarioSchema.model_validate(data)
