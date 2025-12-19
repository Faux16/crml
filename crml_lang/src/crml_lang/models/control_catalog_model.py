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
    ref: Optional[ControlStructuredRef] = Field(
        None, description="Optional structured locator to map the id to an external standard."
    )
    title: Optional[str] = Field(None, description="Optional short human-readable title for the control.")
    url: Optional[str] = Field(None, description="Optional URL for additional reference material.")
    tags: Optional[List[str]] = Field(None, description="Optional list of tags for grouping/filtering.")
    defense_in_depth_layers: Optional[List[Literal["prevent", "detect", "respond", "recover"]]] = Field(
        None,
        description=(
            "Optional defense-in-depth layer tags. Allowed values: prevent, detect, respond, recover."
        ),
    )


class ControlCatalog(BaseModel):
    id: Optional[str] = Field(None, description="Optional identifier for this catalog (organization-owned).")
    # Free-form label for humans/tools (e.g. "CIS v8", "ISO 27001:2022").
    framework: str = Field(..., description="Free-form framework label for humans/tools.")
    controls: List[ControlCatalogEntry] = Field(..., description="List of catalog entries.")


class CRControlCatalog(BaseModel):
    crml_control_catalog: Literal["1.0"] = Field(
        ..., description="Control catalog document version identifier."
    )
    meta: Meta = Field(..., description="Document metadata (name, description, tags, etc.).")
    catalog: ControlCatalog = Field(..., description="The control catalog payload.")

    model_config: ConfigDict = ConfigDict(populate_by_name=True)
