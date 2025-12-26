from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class OscalControlTextOptions:
    """Options to control how OSCAL control text is mapped into CRML fields.

    This is intentionally small and focused: it only governs how we build the
    CRML `description` from OSCAL `prose` and `parts[].prose`.

    If `include_part_names` is None, the converter will keep the legacy behavior:
    include control.prose and all parts' prose recursively.
    """

    include_part_names: Optional[set[str]] = None
    include_control_prose: bool = False

    objective_heading: Optional[str] = None
    bullet_objectives: bool = True
    include_objective_ids: bool = True
