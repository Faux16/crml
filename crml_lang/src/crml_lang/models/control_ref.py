from __future__ import annotations

from typing import Annotated, Optional, Union

from pydantic import BaseModel, Field, field_validator


"""Control identifier primitives.

CRML control identifiers must be *standard independent*.

Design goals:
- Scenarios can reference controls by a stable, unique id.
- Portfolios can import control assessment outputs from any framework/tool.

We keep the id rule intentionally permissive (non-whitespace string) because
different standards and tools use very different identifier shapes.
"""


ControlId = Annotated[
    str,
    Field(
        min_length=1,
        max_length=256,
        pattern=r"^\S+$",
        description="Canonical unique control id (non-whitespace string). Examples: cis.v8.2.3, iso27001:2022:A.5.1, hipaa.164.308(a)(1)(ii)(A)",
    ),
]


class ControlStructuredRef(BaseModel):
    """Standard-independent structured control locator.

    This is optional metadata that can be used by tools/UI to help users map
    controls, but *referencing* in scenarios/portfolios should be done via
    `ControlId`.

    Example:
        {standard: "CIS", version: "v8", control: "2", safeguard: "3"}
    """

    standard: str
    version: Optional[str] = None
    control: str
    safeguard: Optional[str] = None

    @field_validator("standard", "version", "control", "safeguard", mode="before")
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
    parts = [ref.standard, ref.version or "", ref.control, ref.safeguard or ""]
    return "|".join(parts)
