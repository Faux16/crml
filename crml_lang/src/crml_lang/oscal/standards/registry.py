from __future__ import annotations

from typing import Optional

from .base import OscalControlTextOptions
from .scf import scf_control_text_options


def detect_standard_id(
    *,
    endpoint_id: Optional[str] = None,
    catalog_id: Optional[str] = None,
) -> Optional[str]:
    """Detect a standard id.

    Current policy (per request): prefix matching.

    - Any endpoint/catalog id starting with 'scf' -> standard_id='scf'
    """

    for value in (endpoint_id, catalog_id):
        if not value:
            continue
        if str(value).strip().lower().startswith("scf"):
            return "scf"

    return None


def get_control_text_options(standard_id: Optional[str]) -> Optional[OscalControlTextOptions]:
    if standard_id == "scf":
        return scf_control_text_options()
    return None
