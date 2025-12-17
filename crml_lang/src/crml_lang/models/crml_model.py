"""crml_model.py

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

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .numberish import parse_floatish, parse_float_list
from .control_ref import ControlId
from .coverage_model import Coverage


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

# --- Model: Frequency ---
FrequencyBasis = Literal["per_organization_per_year", "per_asset_unit_per_year"]

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
    alpha_base: Optional[float] = Field(None, description="Frequency model parameter (model-specific).")
    beta_base: Optional[float] = Field(None, description="Frequency model parameter (model-specific).")
    r: Optional[float] = Field(None, description="Frequency model parameter (model-specific).")
    p: Optional[float] = Field(None, description="Probability parameter for frequency model (0..1).")

    @field_validator('lambda_', 'alpha_base', 'beta_base', 'r', mode='before')
    @classmethod
    def _parse_numbers_no_percent(cls, v):
        if v is None:
            return None
        return parse_floatish(v, allow_percent=False)

    @field_validator('p', mode='before')
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
    model: str = Field(..., description="Frequency distribution/model identifier (engine-defined).")
    parameters: FrequencyParameters = Field(..., description="Model parameters for the selected frequency model.")

# --- Model: Severity ---
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
    shape: Optional[float] = Field(None, description="Distribution parameter (model-specific).")
    scale: Optional[float] = Field(None, description="Distribution parameter (model-specific).")
    alpha: Optional[float] = Field(None, description="Distribution parameter (model-specific).")
    x_min: Optional[float] = Field(None, description="Minimum loss / truncation parameter (model-specific).")
    single_losses: Optional[List[float]] = Field(
        None,
        description="Optional list of explicit sample losses (used by some empirical severity models).",
    )

    @field_validator('median', 'sigma', 'shape', 'scale', 'alpha', 'x_min', mode='before')
    @classmethod
    def _parse_numbers_no_percent(cls, v):
        if v is None:
            return None
        return parse_floatish(v, allow_percent=False)

    @field_validator('single_losses', mode='before')
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
    implementation_effectiveness: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Scenario-scoped implementation effectiveness override (0..1).",
    )

    potency: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description=(
            "Scenario-scoped potency factor for this control against this specific threat (0..1). "
            "This represents how strong the control is against the scenario if implemented and applied; "
            "it is multiplied with portfolio/assessment posture values during planning."
        ),
    )
    coverage: Optional[Coverage] = Field(
        None,
        description="Scenario-scoped coverage override (breadth of deployment/application).",
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


# Backward-compatible alias used by the engine/tests.
CRMLSchema = CRScenarioSchema

# Usage: CRScenarioSchema.model_validate(your_json_dict)


def load_crml_from_yaml(path: str) -> CRScenarioSchema:
    """Load a CRML Scenario YAML file from `path` and validate it.

    Requires PyYAML (`pip install pyyaml`).
    """
    try:
        import yaml
    except Exception as e:
        raise ImportError('PyYAML is required to load YAML files: pip install pyyaml') from e

    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    return CRScenarioSchema.model_validate(data)


def load_crml_from_yaml_str(yaml_text: str) -> CRScenarioSchema:
    """Load a CRML Scenario document from a YAML string and validate."""
    try:
        import yaml
    except Exception as e:
        raise ImportError('PyYAML is required to load YAML files: pip install pyyaml') from e

    data = yaml.safe_load(yaml_text)
    return CRScenarioSchema.model_validate(data)