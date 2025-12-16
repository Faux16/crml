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
from pydantic import BaseModel, Field, ConfigDict, field_validator

from .numberish import parse_floatish, parse_float_list
from .control_ref import ControlId
from .coverage_model import Coverage


# --- $defs ---
class ISO3166Alpha2(str):
    pass

# --- Meta ---
class Meta(BaseModel):
    name: str
    version: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    organization: Optional[str] = None
    industries: Optional[List[str]] = None
    locale: Dict[str, Any] = Field(default_factory=dict)
    company_sizes: Optional[List[str]] = None
    regulatory_frameworks: Optional[List[str]] = None
    tags: Optional[List[str]] = None

# --- Data ---
class DataSource(BaseModel):
    type: str
    data_schema: Optional[Dict[str, str]] = None

class Data(BaseModel):
    sources: Optional[Dict[str, DataSource]] = None
    feature_mapping: Optional[Dict[str, str]] = None

# --- Model: Frequency ---
FrequencyBasis = Literal["per_organization_per_year", "per_asset_unit_per_year"]

class FrequencyParameters(BaseModel):
    lambda_: Optional[float] = Field(None, alias="lambda")
    alpha_base: Optional[float] = None
    beta_base: Optional[float] = None
    r: Optional[float] = None
    p: Optional[float] = None

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
    basis: FrequencyBasis = "per_organization_per_year"
    model: str
    parameters: FrequencyParameters

# --- Model: Severity ---
class SeverityParameters(BaseModel):
    median: Optional[float] = None
    currency: Optional[str] = None
    mu: Optional[float] = None
    sigma: Optional[float] = None
    shape: Optional[float] = None
    scale: Optional[float] = None
    alpha: Optional[float] = None
    x_min: Optional[float] = None
    single_losses: Optional[List[float]] = None

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
    model: str
    parameters: SeverityParameters
    components: Optional[List[Dict[str, Any]]] = None


class ScenarioControl(BaseModel):
    """Scenario-specific control reference.

    This allows a scenario to specify scenario-scoped assumptions for a control
    (e.g. partial applicability) without requiring portfolio-wide changes.
    """

    id: ControlId
    implementation_effectiveness: Optional[float] = Field(None, ge=0.0, le=1.0)
    coverage: Optional[Coverage] = None
    notes: Optional[str] = None


class Scenario(BaseModel):
    frequency: Frequency
    severity: Severity
    # Threat-centric declaration of relevant controls.
    # Semantics: "This threat can be mitigated by these controls (if present in the portfolio)".
    controls: Optional[List[Union[ControlId, ScenarioControl]]] = None


# --- Root CRML Scenario Schema ---
class CRScenarioSchema(BaseModel):
    crml_scenario: Literal["1.2"]
    meta: Meta
    data: Optional[Data] = None
    scenario: Scenario

    # Pydantic v2 config
    model_config: ConfigDict = ConfigDict(populate_by_name=True)

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