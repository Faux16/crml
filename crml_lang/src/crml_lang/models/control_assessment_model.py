from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from .control_ref import ControlId, ControlStructuredRef
from .coverage_model import Coverage
from .crml_model import Meta


class ControlAssessment(BaseModel):
    id: ControlId
    ref: Optional[ControlStructuredRef] = None

    # Organization-specific posture/implementation strength for this control.
    # Semantics: 0.0 = not implemented / no coverage, 1.0 = fully implemented.
    implementation_effectiveness: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Breadth of deployment/application across the organization.
    coverage: Optional[Coverage] = None

    notes: Optional[str] = None


class ControlAssessmentPack(BaseModel):
    # Controls assessment packs are organization-owned artifacts.
    # They capture "what do we have" and optionally "how well".
    id: Optional[str] = None
    # Free-form label for humans/tools (e.g. "CISv8", "ISO27001:2022", "HIPAA").
    framework: str
    assessments: List[ControlAssessment]


class CRControlAssessmentSchema(BaseModel):
    crml_control_assessment: Literal["1.0"]
    meta: Meta
    assessment: ControlAssessmentPack

    model_config: ConfigDict = ConfigDict(populate_by_name=True)
