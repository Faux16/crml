from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


CoverageBasis = Literal[
    "endpoints",
    "employees",
    "servers",
    "applications",
    "business_units",
    "data_stores",
    "other",
]


class Coverage(BaseModel):
    """Breadth of application of a control across an organization.

    Semantics:
    - value=0.0 means "not deployed/applied anywhere in the stated basis"
    - value=1.0 means "fully deployed/applied across the stated basis"

    The basis defines the denominator for the fraction (e.g. endpoints, employees).
    """

    value: float = Field(
        ..., ge=0.0, le=1.0, description="Coverage fraction in [0, 1] for the stated basis."
    )
    basis: CoverageBasis = Field(
        ..., description="Coverage basis/denominator (e.g. endpoints, employees)."
    )
    notes: Optional[str] = Field(None, description="Optional free-form notes about how coverage was estimated.")
