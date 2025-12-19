from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import AliasChoices, BaseModel, Field

from .scenario_model import CRScenario
from .portfolio_model import CRPortfolio
from .control_catalog_model import CRControlCatalog
from .assessment_model import CRAssessment
from .control_relationships_model import CRControlRelationships
from .attack_catalog_model import CRAttackCatalog
from .attack_control_relationships_model import CRAttackControlRelationships


class BundleMessage(BaseModel):
    level: Literal["error", "warning"] = Field(..., description="Message severity level.")
    path: str = Field(..., description="Logical document path where the issue occurred.")
    message: str = Field(..., description="Human-readable message.")

class BundledScenario(BaseModel):
    id: str = Field(..., description="Scenario id from the portfolio.")
    weight: Optional[float] = Field(None, description="Optional scenario weight (portfolio semantics dependent).")

    # Traceability only; engines should not require filesystem access.
    source_path: Optional[str] = Field(None, description="Original scenario path reference (if any).")

    scenario: CRScenario = Field(..., description="Inlined, validated CRML scenario document.")


class PortfolioBundlePayload(BaseModel):
    """Portfolio bundle payload for `CRPortfolioBundle`.

    This is intentionally the inlined artifact content; engines should not require filesystem access.
    """

    portfolio: CRPortfolio = Field(..., description="The CRML portfolio document.")

    scenarios: List[BundledScenario] = Field(
        default_factory=list,
        description="Scenario documents referenced by the portfolio, inlined.",
    )

    control_catalogs: List[CRControlCatalog] = Field(
        default_factory=list,
        description="Optional inlined control catalog packs referenced by the portfolio.",
    )

    assessments: List[CRAssessment] = Field(
        default_factory=list,
        validation_alias=AliasChoices("assessments"),
        serialization_alias="assessments",
        description="Optional inlined assessment packs referenced by the portfolio.",
    )

    control_relationships: List[CRControlRelationships] = Field(
        default_factory=list,
        description="Optional inlined control relationships packs referenced by the portfolio.",
    )

    attack_catalogs: List[CRAttackCatalog] = Field(
        default_factory=list,
        description="Optional inlined attack catalogs (e.g., MITRE ATT&CK) referenced by the portfolio.",
    )

    attack_control_relationships: List[CRAttackControlRelationships] = Field(
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
