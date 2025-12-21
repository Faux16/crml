from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from .control_ref import ControlId, ControlStructuredRef
from .scenario_model import Meta


class ControlCatalogEntry(BaseModel):
    """Portable metadata about a control id.

    Important: do not embed copyrighted standard text here.
    Keep this to identifiers and tool-friendly metadata.
    """

    id: ControlId = Field(..., description="Canonical unique control id present in this catalog.")
    oscal_uuid: Optional[str] = Field(
        None,
        description=(
            "Optional OSCAL UUID for this control. This is interoperability metadata only; "
            "CRML tools should continue to reference this control via the canonical 'id'."
        ),
    )
    ref: Optional[ControlStructuredRef] = Field(
        None, description="Optional structured locator to map the id to an external standard."
    )
    title: Optional[str] = Field(None, description="Optional short human-readable title for the control.")
    description: Optional[str] = Field(
        None,
        description=(
            "Optional free-form description text for this control entry. "
            "Only include standard/control prose if you have rights to distribute it."
        ),
    )
    url: Optional[str] = Field(None, description="Optional URL for additional reference material.")
    tags: Optional[List[str]] = Field(None, description="Optional list of tags for grouping/filtering.")
    defense_in_depth_layers: Optional[List[Literal["prevent", "detect", "respond", "recover"]]] = Field(
        None,
        description=(
            "Optional defense-in-depth layer tags. Allowed values: prevent, detect, respond, recover."
        ),
    )


class ControlCatalogGroup(BaseModel):
    """Optional hierarchical grouping for control catalogs.

    Designed to represent OSCAL `groups[]` without duplicating control objects.
    """

    id: str = Field(..., description="Group identifier (OSCAL group id).")
    oscal_uuid: Optional[str] = Field(
        None,
        description=(
            "Optional OSCAL UUID for this group (interoperability metadata). "
            "CRML tooling should continue to reference groups by their in-document 'id'."
        ),
    )
    title: Optional[str] = Field(None, description="Optional human-readable group title.")
    description: Optional[str] = Field(
        None,
        description=(
            "Optional free-form description text for this group. "
            "If sourced from OSCAL, this typically maps from group prose/parts. "
            "Only include copyrighted standard text if you have rights to distribute it."
        ),
    )
    control_ids: Optional[List[ControlId]] = Field(
        None, description="Optional list of control ids that belong to this group."
    )
    groups: Optional[List[ControlCatalogGroup]] = Field(
        None, description="Optional nested sub-groups (recursive)."
    )


class ControlCatalog(BaseModel):
    id: Optional[str] = Field(None, description="Optional identifier for this catalog (organization-owned).")
    oscal_uuid: Optional[str] = Field(
        None,
        description=(
            "Optional OSCAL UUID for the source catalog (interoperability metadata). "
            "CRML tooling should continue to reference the catalog via 'catalog.id' and controls via canonical 'id'."
        ),
    )
    # Free-form label for humans/tools (e.g. "CIS v8", "ISO 27001:2022").
    framework: str = Field(..., description="Free-form framework label for humans/tools.")
    controls: List[ControlCatalogEntry] = Field(..., description="List of catalog entries.")
    groups: Optional[List[ControlCatalogGroup]] = Field(
        None,
        description=(
            "Optional hierarchical group structure (e.g., OSCAL groups). "
            "Groups reference controls by id via 'control_ids'."
        ),
    )


class CRControlCatalog(BaseModel):
    crml_control_catalog: Literal["1.0"] = Field(
        ..., description="Control catalog document version identifier."
    )
    meta: Meta = Field(..., description="Document metadata (name, description, tags, etc.).")
    catalog: ControlCatalog = Field(..., description="The control catalog payload.")

    model_config = ConfigDict(populate_by_name=True)
