from typing import List, Optional
import pydantic
from pydantic import BaseModel, Field

from .control_ref import ControlId

class AttackStage(BaseModel):
    """A single stage in an attack chain (e.g. 'Initial Access')."""
    
    name: str = Field(..., description="Name of the attack stage (e.g. 'Initial Access').")
    probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Baseline probability of successful progression through this stage (0.0 - 1.0).",
    )
    controls: Optional[List[ControlId]] = Field(
        None,
        description=(
            "List of controls relevant to mitigating this specific stage. "
            "Identifiers must be OSCAL-aligned (e.g. 'nist.sp.800-53:ac-1')."
        ),
    )
    description: Optional[str] = Field(None, description="Optional description of the stage.")

class AttackChain(BaseModel):
    """A sequential chain of attack stages (e.g. Kill Chain)."""
    
    stages: List[AttackStage] = Field(
        ...,
        min_length=1,
        description="Ordered list of attack stages. The chain is traversed sequentially.",
    )
