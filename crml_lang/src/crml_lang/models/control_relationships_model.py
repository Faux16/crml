from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from .control_ref import ControlId
from .crml_model import Meta


class Grouping(BaseModel):
    """Optional taxonomy/grouping tag.

    This is intentionally framework-agnostic.

    Example:
        {scheme: "nist_csf_function", id: "PR", label: "Protect"}
    """

    scheme: str = Field(
        ..., description="Grouping scheme identifier (tool/community-defined). Example: 'nist_csf_function'."
    )
    id: str = Field(..., description="Identifier within the grouping scheme. Example: 'PR'.")
    label: Optional[str] = Field(None, description="Optional human-friendly label for the grouping id.")


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


class Overlap(BaseModel):
    """Quantitative overlap metadata used for downstream math.

    Semantics (recommended):
    - weight: fraction of source coverage provided by the target in [0, 1]
    """

    weight: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Quantitative overlap/coverage weight in [0, 1]. Recommended semantics: the fraction of the "
            "source control's mitigation objective that is covered by the target control."
        ),
    )
    dimensions: Optional[Dict[str, float]] = Field(
        None,
        description=(
            "Optional multidimensional overlap weights (dimension_name -> weight in [0, 1]). "
            "Dimension names are tool/community-defined (e.g. 'coverage', 'intent', 'implementation')."
        ),
    )
    rationale: Optional[str] = Field(
        None,
        description=(
            "Optional free-form rationale explaining why the overlap weight(s) were chosen. "
            "Avoid embedding copyrighted standard text unless you have rights."
        ),
    )


class ControlRelationship(BaseModel):
    """A directed relationship edge between two canonical control ids.

    Intended use:
    - A scenario references a (source) control A.
    - A portfolio implements a (target) control B.
    - This edge expresses how B relates to A (e.g. overlaps/equivalent_to) with quantitative overlap metadata.
    """

    source: ControlId = Field(
        ..., description="Source control id (often scenario/threat-centric)."
    )
    target: ControlId = Field(
        ..., description="Target control id (often portfolio/implementation-centric)."
    )

    relationship_type: Literal[
            "overlaps_with",
            "mitigates",
            "supports",
            "equivalent_to",
            "parent_of",
            "child_of",
        ] = Field(
        None,
        description=(
            "Optional relationship type. Values: 'overlaps_with', 'mitigates', 'supports', 'equivalent_to', "
            "'parent_of', 'child_of'."
        ),
    )

    overlap: Overlap = Field(
        ..., description="Required quantitative overlap metadata for downstream math."
    )

    confidence: float = Field(
        None,
        ge=0.0,
        le=1.0,
        description=(
            "Optional confidence score in [0, 1] for this mapping/relationship (community/org-defined)."
        ),
    )

    groupings: Optional[List[Grouping]] = Field(
        None,
        description=(
            "Optional taxonomy/grouping tags for this relationship (framework-agnostic). "
            "Example: NIST CSF Function classification."
        ),
    )

    description: Optional[str] = Field(
        None,
        description=(
            "Optional description of how/why the target relates to the source. "
            "Avoid embedding copyrighted standard text unless you have rights."
        ),
    )

    references: Optional[List[Reference]] = Field(
        None,
        description="Optional list of references/citations supporting this relationship.",
    )


class ControlRelationshipsPack(BaseModel):
    """Relationship pack payload.

    This is a standalone, shareable dataset that can be community- or org-authored.
    """

    id: Optional[str] = Field(
        None,
        description="Optional identifier for this relationships pack (organization/community-owned).",
    )
    relationships: List[ControlRelationship] = Field(
        ..., description="List of directed control relationship edges."
    )


class CRControlRelationshipsSchema(BaseModel):
    crml_control_relationships: Literal["1.0"] = Field(
        ..., description="Control relationships document version identifier."
    )
    meta: Meta = Field(..., description="Document metadata (name, description, tags, etc.).")
    relationships: ControlRelationshipsPack = Field(
        ..., description="The control relationships payload."
    )

    model_config: ConfigDict = ConfigDict(populate_by_name=True)
