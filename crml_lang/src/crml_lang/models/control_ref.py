from __future__ import annotations

from typing import Annotated, Optional, Union

from pydantic import BaseModel, Field, field_validator


"""Control identifier primitives.

CRML control identifiers must be *standard independent*.

Design goals:
- Scenarios can reference controls by a stable, unique id.
- Portfolios can import assessment outputs from any framework/tool.

Canonical format:
- `namespace:key`
    - namespace: lowercase [a-z0-9_-], starting with a letter
    - key: any non-whitespace sequence (standard-specific)

Examples:
- cap:edr
- cisv8:4.2
- iso27001:2022:A.5.1
"""


ControlId = Annotated[
    str,
    Field(
        min_length=1,
        max_length=256,
        pattern=r"^[a-z][a-z0-9_-]{0,31}:[^\s]{1,223}$",
        description="Canonical unique control id in the form 'namespace:key' (no whitespace). Examples: cap:edr, cisv8:4.2, iso27001:2022:A.5.1",
    ),
]


class ControlStructuredRef(BaseModel):
    """Standard-independent structured control locator.

    This is optional metadata that can be used by tools/UI to help users map
    controls, but *referencing* in scenarios/portfolios should be done via
    `ControlId`.

    Example:
        {standard: "CIS", control: "2", requirement: "Ensure X is implemented"}
    """

    standard: str = Field(..., description="Standard identifier (e.g. CISv8, ISO27001).")
    control: str = Field(..., description="Control identifier within the referenced standard.")
    requirement: Optional[str] = Field(
        None,
        description="Optional requirement text (what the requirement specifies) within the referenced standard (if applicable and not copyrighted).",
    )

    @field_validator("standard", "control", "requirement", mode="before")
    @classmethod
    def _coerce_to_str(cls, v):
        if v is None:
            return None
        return str(v)


# A control reference can be either the canonical string id or the structured form.
ControlRef = Union[ControlId, ControlStructuredRef]


def control_ref_to_id(ref: ControlRef) -> str:
    """Best-effort normalization for duplicate detection.

    If the reference is already an id string, return it.
    If it is structured, return a deterministic composite key.

    NOTE: This is *not* intended to define a universal canonicalization scheme
    across all standards.
    """

    if isinstance(ref, str):
        return ref

    # Composite key that tolerates arbitrary characters.
    parts = [ref.standard, ref.control, ref.requirement or ""]
    return "|".join(parts)
