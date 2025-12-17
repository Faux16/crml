from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from .control_ref import ControlId, ControlStructuredRef
from .coverage_model import Coverage
from .crml_model import Meta


class ControlAssessment(BaseModel):
    id: ControlId = Field(
        ..., description="Canonical unique control id in the form 'namespace:key' (no whitespace)."
    )
    ref: Optional[ControlStructuredRef] = Field(
        None,
        description=(
            "Optional structured locator for mapping to an external standard (e.g. CIS/ISO). "
            "This is metadata only; referencing should use the canonical 'id'."
        ),
    )

    # Organization-specific posture/implementation strength for this control.
    # Semantics: 0.0 = not implemented / no coverage, 1.0 = fully implemented.
    implementation_effectiveness: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description=(
            "Organization-specific implementation strength for this control. "
            "Semantics: 0.0 = not implemented / no coverage, 1.0 = fully implemented."
        ),
    )

    # Breadth of deployment/application across the organization.
    coverage: Optional[Coverage] = Field(
        None, description="Breadth of deployment/application across the organization."
    )

    # Reliability/uptime of the control as a probability of being effective in a given period.
    reliability: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description=(
            "Reliability/uptime of the control as a probability of being effective in a given period."
        ),
    )

    # Effect surface for this control. Default is frequency-first.
    affects: Optional[Literal["frequency", "severity", "both"]] = Field(
        "frequency",
        description=(
            "Which loss component this control affects. "
            "Default is 'frequency' (frequency-first)."
        ),
    )

    notes: Optional[str] = Field(None, description="Free-form notes about this assessment entry.")


class ControlAssessmentPack(BaseModel):
    # Controls assessment packs are organization-owned artifacts.
    # They capture "what do we have" and optionally "how well".
    id: Optional[str] = Field(
        None, description="Optional identifier for this assessment pack (organization-owned)."
    )
    # Free-form label for humans/tools (e.g. "CISv8", "ISO27001:2022", "HIPAA").
    framework: str = Field(
        ..., description="Free-form framework label for humans/tools (e.g. 'CISv8', 'ISO27001:2022')."
    )
    # When this assessment was performed (ISO 8601, e.g. "2025-12-17T12:34:56Z").
    assessed_at: Optional[datetime] = Field(
        None,
        description=(
            "When this assessment pack was performed/recorded (ISO 8601 date-time). "
            "Example: '2025-12-17T10:15:30Z'."
        ),
    )
    assessments: List[ControlAssessment] = Field(
        ..., description="List of per-control assessment entries."
    )


class CRControlAssessmentSchema(BaseModel):
    crml_control_assessment: Literal["1.0"] = Field(
        ..., description="Control assessment document version identifier."
    )
    meta: Meta = Field(..., description="Document metadata (name, description, tags, etc.).")
    assessment: ControlAssessmentPack = Field(
        ..., description="The control assessment pack payload."
    )

    model_config: ConfigDict = ConfigDict(populate_by_name=True)
