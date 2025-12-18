from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import AliasChoices, BaseModel, Field

from .crml_model import CRScenarioSchema
from .portfolio_model import CRPortfolioSchema
from .control_catalog_model import CRControlCatalogSchema
from .assessment_model import CRAssessmentSchema
from .control_relationships_model import CRControlRelationshipsSchema
from .attack_catalog_model import CRAttackCatalogSchema
from .attack_control_relationships_model import CRAttackControlRelationshipsSchema


class BundleMessage(BaseModel):
    level: Literal["error", "warning"] = Field(..., description="Message severity level.")
    path: str = Field(..., description="Logical document path where the issue occurred.")
    message: str = Field(..., description="Human-readable message.")

class BundledScenario(BaseModel):
    id: str = Field(..., description="Scenario id from the portfolio.")
    weight: Optional[float] = Field(None, description="Optional scenario weight (portfolio semantics dependent).")

    # Traceability only; engines should not require filesystem access.
    source_path: Optional[str] = Field(None, description="Original scenario path reference (if any).")

    scenario: CRScenarioSchema = Field(..., description="Inlined, validated CRML scenario document.")


class PortfolioBundlePayload(BaseModel):
    """Portfolio bundle payload for `CRPortfolioBundle`.

    This is intentionally the inlined artifact content; engines should not require filesystem access.
    """

    portfolio: CRPortfolioSchema = Field(..., description="The CRML portfolio document.")

    scenarios: List[BundledScenario] = Field(
        default_factory=list,
        description="Scenario documents referenced by the portfolio, inlined.",
    )

    control_catalogs: List[CRControlCatalogSchema] = Field(
        default_factory=list,
        description="Optional inlined control catalog packs referenced by the portfolio.",
    )

    assessments: List[CRAssessmentSchema] = Field(
        default_factory=list,
        validation_alias=AliasChoices("assessments", "control_assessments"),
        serialization_alias="assessments",
        description="Optional inlined assessment packs referenced by the portfolio.",
    )

    control_relationships: List[CRControlRelationshipsSchema] = Field(
        default_factory=list,
        description="Optional inlined control relationships packs referenced by the portfolio.",
    )

    attack_catalogs: List[CRAttackCatalogSchema] = Field(
        default_factory=list,
        description="Optional inlined attack catalogs (e.g., MITRE ATT&CK) referenced by the portfolio.",
    )

    attack_control_relationships: List[CRAttackControlRelationshipsSchema] = Field(
        default_factory=list,
        description="Optional inlined attack-to-control relationships mappings referenced by the portfolio.",
    )

    warnings: List[BundleMessage] = Field(default_factory=list, description="Non-fatal bundle warnings.")

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional metadata for traceability (e.g., source refs). Not interpreted by engines.",
    )


class CRPortfolioBundle(BaseModel):
    """Engine-agnostic bundle produced by the language layer.

    A portfolio bundle is a single, self-contained artifact that contains:
    - the portfolio document
    - referenced scenario documents inlined
    - optionally, referenced control packs inlined

    The bundle is intended as the contract between `crml_lang` and engines.
    """

    crml_portfolio_bundle: Literal["1.0"] = Field(
        "1.0",
        description="Portfolio bundle document version identifier.",
    )

    portfolio_bundle: PortfolioBundlePayload = Field(
        ..., description="The portfolio bundle payload (inlined artifact content)."
    )
