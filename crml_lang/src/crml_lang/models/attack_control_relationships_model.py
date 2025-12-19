from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from .control_ref import ControlId
from .scenario_model import AttckId, Meta


class Reference(BaseModel):
    """Optional reference/citation for a relationship.

    Keep this to pointers and provenance. Avoid embedding copyrighted standard text unless you have rights.
    """

    type: str = Field(
        ..., description="Reference type discriminator (e.g. 'url', 'document', 'ticket', 'evidence')."
    )
    label: Optional[str] = Field(None, description="Optional short label for this reference.")
    url: Optional[str] = Field(None, description="Optional URL for this reference.")
    citation: Optional[str] = Field(None, description="Optional citation string (free-form).")


AttackControlRelationshipType = Literal[
    "mitigated_by",
    "detectable_by",
    "respondable_by",
]


class AttackControlTarget(BaseModel):
    """One target control mapped from an attack pattern."""

    control: ControlId = Field(..., description="Target control id.")

    relationship_type: AttackControlRelationshipType = Field(
        ..., description="Relationship type between the attack pattern and the control."
    )

    strength: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description=(
            "Optional quantitative strength in [0, 1] indicating how strongly this control mitigates/detects/responds "
            "to the attack pattern (tool/community-defined semantics)."
        ),
    )

    confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Optional confidence score in [0, 1] for this mapping (tool/community-defined).",
    )

    description: Optional[str] = Field(
        None,
        description=(
            "Optional description of how/why the control relates to the attack pattern. "
            "Avoid embedding copyrighted standard text unless you have rights."
        ),
    )

    references: Optional[List[Reference]] = Field(
        None, description="Optional list of references/citations supporting this mapping."
    )

    tags: Optional[List[str]] = Field(None, description="Optional list of tags for grouping/filtering.")


class AttackControlRelationship(BaseModel):
    """Grouped relationship mapping for a single attack pattern id."""

    attack: AttckId = Field(..., description="Source attack-pattern id (recommended namespace: 'attck').")

    targets: List[AttackControlTarget] = Field(
        ..., min_length=1, description="List of mapped controls for this attack pattern."
    )


class AttackControlRelationshipsPack(BaseModel):
    """Relationship pack payload.

    This is a standalone, shareable dataset that can be community- or org-authored.
    """

    id: Optional[str] = Field(
        None, description="Optional identifier for this relationships pack (organization/community-owned)."
    )

    relationships: List[AttackControlRelationship] = Field(
        ..., description="List of grouped attack-to-control relationship mappings."
    )

    metadata: Optional[Dict[str, str]] = Field(
        None,
        description=(
            "Optional free-form metadata for tools (e.g., source dataset name/version). "
            "Not interpreted by validators/engines."
        ),
    )


class CRAttackControlRelationships(BaseModel):
    crml_attack_control_relationships: Literal["1.0"] = Field(
        ..., description="Attack-to-control relationships document version identifier."
    )
    meta: Meta = Field(..., description="Document metadata (name, description, tags, etc.).")
    relationships: AttackControlRelationshipsPack = Field(
        ..., description="The attack-to-control relationships payload."
    )

    model_config: ConfigDict = ConfigDict(populate_by_name=True)
