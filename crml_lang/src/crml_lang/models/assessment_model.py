from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .control_ref import ControlId, ControlStructuredRef
from .coverage_model import Coverage
from .scenario_model import Meta


class Assessment(BaseModel):
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

    implementation_effectiveness: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description=(
            "Organization-specific implementation strength for this control. "
            "Semantics: 0.0 = not implemented / no coverage, 1.0 = fully implemented. "
            "This represents vulnerability likelihood (susceptibility) posture used to mitigate a scenario's baseline threat frequency."
        ),
    )

    coverage: Optional[Coverage] = Field(
        None,
        description=(
            "Breadth of deployment/application across the organization. This contributes to vulnerability likelihood reduction "
            "when applying this control to a scenario."
        ),
    )

    reliability: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Reliability/uptime of the control as a probability of being effective in a given period.",
    )

    affects: Optional[Literal["frequency", "severity", "both"]] = Field(
        "frequency",
        description=(
            "Which loss component this assessment affects. "
            "Default is 'frequency' (frequency-first). Note: the current reference engine primarily applies controls to frequency (lambda)."
        ),
    )

    scf_cmm_level: Optional[int] = Field(
        None,
        ge=0,
        le=5,
        description=(
            "SCF Capability Maturity Model (CMM) level for this control (0..5). "
            "Levels: 0=Not Performed, 1=Performed Informally, 2=Planned & Tracked, 3=Well-Defined, "
            "4=Quantitatively Controlled, 5=Continuously Improving."
        ),
    )

    question: Optional[str] = Field(
        None,
        description=(
            "Optional assessment prompt/question text for this control (tool/community-defined). "
            "Useful for questionnaires and evidence collection."
        ),
    )

    description: Optional[str] = Field(
        None,
        description=(
            "Optional additional description for this assessment entry (tool/community-defined). "
            "Avoid embedding copyrighted standard text unless you have rights."
        ),
    )

    notes: Optional[str] = Field(None, description="Free-form notes about this assessment entry.")

    @model_validator(mode="after")
    def _validate_answer_mode(self) -> "Assessment":
        has_cmm = self.scf_cmm_level is not None
        has_quantitative = any(
            v is not None
            for v in (
                self.implementation_effectiveness,
                self.coverage,
                self.reliability,
            )
        )

        if has_cmm and has_quantitative:
            raise ValueError(
                "Assessment entry must use either scf_cmm_level (SCF CMM) OR quantitative posture fields "
                "(implementation_effectiveness/coverage/reliability), but not both."
            )

        if not has_cmm and not has_quantitative:
            raise ValueError(
                "Assessment entry must provide either scf_cmm_level (SCF CMM) or at least one of "
                "implementation_effectiveness, coverage, reliability."
            )

        return self

    model_config: ConfigDict = ConfigDict(extra="forbid")


class AssessmentCatalog(BaseModel):
    id: Optional[str] = Field(
        None, description="Optional identifier for this assessment catalog (organization-owned)."
    )
    framework: str = Field(
        ..., description="Free-form framework label for humans/tools (e.g. 'CISv8', 'ISO27001:2022')."
    )
    assessed_at: Optional[datetime] = Field(
        None,
        description=(
            "When this assessment catalog was performed/recorded (ISO 8601 date-time). "
            "Example: '2025-12-17T10:15:30Z'."
        ),
    )
    assessments: List[Assessment] = Field(..., description="List of per-control assessment entries.")

    model_config: ConfigDict = ConfigDict(extra="forbid")


class CRAssessment(BaseModel):
    crml_assessment: Literal["1.0"] = Field(
        ...,
        description="Assessment document version identifier.",
    )
    meta: Meta = Field(..., description="Document metadata (name, description, tags, etc.).")
    assessment: AssessmentCatalog = Field(..., description="The assessment catalog payload.")

    model_config: ConfigDict = ConfigDict(populate_by_name=True, extra="forbid")
