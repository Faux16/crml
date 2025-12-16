from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator

from .crml_model import Meta
from .control_ref import ControlId
from .coverage_model import Coverage
from .numberish import parse_intish


class CriticalityIndex(BaseModel):
    type: Optional[str] = None
    inputs: Optional[Dict[str, str]] = None
    weights: Optional[Dict[str, float]] = None
    transform: Optional[str] = None


class Asset(BaseModel):
    name: str
    cardinality: int = Field(..., ge=1)
    criticality_index: Optional[CriticalityIndex] = None
    tags: Optional[List[str]] = None

    @field_validator("cardinality", mode="before")
    @classmethod
    def _parse_cardinality(cls, v):
        return parse_intish(v)


PortfolioMethod = Literal["sum", "mixture", "choose_one", "max"]


class PortfolioConstraints(BaseModel):
    require_paths_exist: bool = False
    validate_scenarios: bool = True


class PortfolioSemantics(BaseModel):
    method: PortfolioMethod
    constraints: PortfolioConstraints = Field(default_factory=PortfolioConstraints)


class ScenarioBinding(BaseModel):
    # Minimal binding surface: explicit list of portfolio asset names.
    # If a scenario is per-asset-unit, this defines its exposure set.
    applies_to_assets: Optional[List[str]] = None


class ScenarioRef(BaseModel):
    id: str
    path: str
    weight: Optional[float] = None
    binding: ScenarioBinding = Field(default_factory=ScenarioBinding)
    tags: Optional[List[str]] = None


class CorrelationRelationship(BaseModel):
    type: Literal["correlation"]
    between: List[str] = Field(..., min_length=2, max_length=2)
    value: float = Field(..., ge=-1.0, le=1.0)
    method: Optional[Literal["gaussian_copula", "rank_correlation"]] = None


class ConditionalRelationship(BaseModel):
    type: Literal["conditional"]
    given: str
    then: str
    probability: float = Field(..., ge=0.0, le=1.0)


Relationship = CorrelationRelationship | ConditionalRelationship


class PortfolioControl(BaseModel):
    # Canonical unique control id, e.g. "cis.v8.2.3" or "iso27001:2022:A.5.1".
    id: ControlId
    implementation_effectiveness: Optional[float] = Field(None, ge=0.0, le=1.0)
    coverage: Optional[Coverage] = None
    notes: Optional[str] = None


class Portfolio(BaseModel):
    assets: List[Asset] = Field(default_factory=list)
    controls: Optional[List[PortfolioControl]] = None
    scenarios: List[ScenarioRef]
    semantics: PortfolioSemantics
    relationships: Optional[List[Relationship]] = None
    context: Dict[str, Any] = Field(default_factory=dict)


class CRPortfolioSchema(BaseModel):
    crml_portfolio: Literal["1.0"]
    meta: Meta
    portfolio: Portfolio

    model_config: ConfigDict = ConfigDict(populate_by_name=True)
