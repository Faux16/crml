"""
crmlModel.py
============

This module defines the core data models for CRML (Cyber Risk Modeling Language) using Pydantic for type safety and validation.

Purpose:
--------
- Provide structured, validated representations of CRML concepts such as assets, frequency, severity, metadata, and data sources.
- Enable attribute-style access and type checking for all model elements used in simulation, validation, and runtime analysis.
- Serve as the schema backbone for parsing, validating, and manipulating CRML YAML/JSON documents in Python code.

Key Model Groups:
-----------------
- Meta: Describes metadata about the model (name, version, author, etc.).
- Data: Describes data sources and feature mappings.
- Asset: Represents assets with cardinality and criticality.
- Frequency/Severity: Parameterize risk event frequency and loss severity, supporting multiple statistical models.
- (Other models may be defined for controls, scenarios, etc.)

Validation:
-----------
- Uses Pydantic validators to parse and normalize numeric/string fields (e.g., cardinality, lambda, percentages).
- Ensures type safety and consistency for downstream simulation and reporting.

Usage:
------
- Import these models in runtime, validator, and CLI modules to load, validate, and process CRML documents.
- Extend or compose these models to support new CRML features or custom fields.

"""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator

# This module (resultModel.py) defines Pydantic models for simulation results, metrics, distribution, and metadata.
# Use these models to enable attribute-style access and type safety for simulation outputs in runtime.py and related modules.

# --- Helper Types ---
NumberOrString = Union[int, float, str]

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

# --- Model: Assets ---
class CriticalityIndex(BaseModel):
    type: Optional[str] = None
    inputs: Optional[Dict[str, str]] = None
    weights: Optional[Dict[str, float]] = None
    transform: Optional[str] = None

class Asset(BaseModel):
    name: str
    cardinality: NumberOrString
    criticality_index: Optional[CriticalityIndex] = None

    @field_validator('cardinality', mode='before')
    @classmethod
    def _parse_cardinality(cls, v):
        if isinstance(v, str):
            s = v.strip().replace(',', '').replace(' ', '')
            try:
                return int(s)
            except Exception:
                try:
                    return float(s)
                except Exception:
                    return v
        return v

# --- Model: Frequency ---
class FrequencyParameters(BaseModel):
    lambda_: Optional[NumberOrString] = Field(None, alias="lambda")
    alpha_base: Optional[NumberOrString] = None
    beta_base: Optional[NumberOrString] = None
    r: Optional[NumberOrString] = None
    p: Optional[NumberOrString] = None

    @staticmethod
    def _parse_numberish_value(v):
        """
        Parse a numeric value that may contain space-separated thousands (ISO 80000-1 thin space or regular space).
        This matches the parse_number logic in runtime.py.
        """
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            s = v.strip().replace(' ', '').replace('\u202f', '').replace(',', '')
            if s.endswith('%'):
                try:
                    return float(s[:-1]) / 100.0
                except Exception:
                    return v
            try:
                return float(s)
            except Exception:
                return v
        return v

    @field_validator('lambda_', 'alpha_base', 'beta_base', 'r', 'p', mode='before')
    @classmethod
    def _parse_numbers(cls, v):
        return cls._parse_numberish_value(v)

class FrequencyModel(BaseModel):
    asset: str
    model: str
    parameters: FrequencyParameters

class Frequency(BaseModel):
    scope: Optional[str] = "portfolio"
    model: Optional[str] = None
    parameters: Optional[FrequencyParameters] = None
    models: Optional[List[FrequencyModel]] = None

# --- Model: Severity ---
class SeverityParameters(BaseModel):
    median: Optional[NumberOrString] = None
    currency: Optional[str] = None
    mu: Optional[float] = None
    sigma: Optional[NumberOrString] = None
    shape: Optional[NumberOrString] = None
    scale: Optional[NumberOrString] = None
    alpha: Optional[NumberOrString] = None
    x_min: Optional[NumberOrString] = None
    single_losses: Optional[List[NumberOrString]] = None

    @staticmethod
    def _parse_numberish_value(v):
        """
        Parse a numeric value that may contain space-separated thousands (ISO 80000-1 thin space or regular space).
        """
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            s = v.strip().replace(' ', '').replace('\u202f', '').replace(',', '')
            if s.endswith('%'):
                try:
                    return float(s[:-1]) / 100.0
                except Exception:
                    return v
            try:
                return float(s)
            except Exception:
                return v
        return v

    @field_validator('median', 'sigma', 'shape', 'scale', 'alpha', 'x_min', mode='before')
    @classmethod
    def _parse_numbers(cls, v):
        return cls._parse_numberish_value(v)

    @field_validator('single_losses', mode='before')
    @classmethod
    def _parse_single_losses(cls, v):
        if isinstance(v, list):
            return [cls._parse_numberish_value(item) for item in v]
        return v

class SeverityModel(BaseModel):
    asset: str
    model: str
    parameters: SeverityParameters

class Severity(BaseModel):
    model: Optional[str] = None
    parameters: Optional[SeverityParameters] = None
    components: Optional[List[Dict[str, Any]]] = None
    models: Optional[List[SeverityModel]] = None


# --- Model: Dependency ---
class Dependency(BaseModel):
    name: str
    depends_on: Optional[List[str]] = None
    type: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None

# --- Model: Controls ---
class Control(BaseModel):
    name: str
    description: Optional[str] = None
    effectiveness: Optional[NumberOrString] = None
    cost: Optional[NumberOrString] = None
    parameters: Optional[Dict[str, Any]] = None

class Controls(BaseModel):
    controls: Optional[List[Control]] = None
    layers: Optional[List[Dict[str, Any]]] = None

# --- Model: Temporal ---
class Temporal(BaseModel):
    time_horizon: Optional[NumberOrString] = None
    granularity: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None

# --- Model: Pipeline ---
class Pipeline(BaseModel):
    steps: Optional[List[Dict[str, Any]]] = None
    parameters: Optional[Dict[str, Any]] = None

# --- Model: Output ---
class Output(BaseModel):
    format: Optional[str] = None
    destination: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class Model(BaseModel):
    assets: List[Asset] = Field(default_factory=list)
    frequency: Optional[Frequency] = None
    severity: Optional[Severity] = None
    dependency: Optional[List[Dependency]] = None
    controls: Optional[Controls] = None
    temporal: Optional[Temporal] = None
    pipeline: Optional[Pipeline] = None
    output: Optional[Output] = None

# --- Root CRML Schema ---
class CRMLSchema(BaseModel):
    crml: str
    meta: Meta
    data: Optional[Data] = None
    model: Model
    pipeline: Optional[Dict[str, Any]] = None
    output: Optional[Dict[str, Any]] = None

    # Pydantic v2 config
    model_config: ConfigDict = ConfigDict(populate_by_name=True)

# Usage: CRMLSchema.parse_obj(your_json_dict)


def load_crml_from_yaml(path: str) -> CRMLSchema:
    """Load a CRML YAML file from `path` and validate it against the Pydantic model.

    Requires PyYAML (`pip install pyyaml`).
    """
    try:
        import yaml
    except Exception as e:
        raise ImportError('PyYAML is required to load YAML files: pip install pyyaml') from e

    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    return CRMLSchema.model_validate(data)


def load_crml_from_yaml_str(yaml_text: str) -> CRMLSchema:
    """Load CRML document from a YAML string and validate."""
    try:
        import yaml
    except Exception as e:
        raise ImportError('PyYAML is required to load YAML files: pip install pyyaml') from e

    data = yaml.safe_load(yaml_text)
    return CRMLSchema.model_validate(data)