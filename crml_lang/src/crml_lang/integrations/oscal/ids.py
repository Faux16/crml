from __future__ import annotations

import uuid

from crml_lang.models.control_ref import ControlId


_CRML_OSCAL_NAMESPACE = uuid.UUID("c5f8d0ff-0e4f-4d9a-99d0-03e4d3cb8e59")


def control_id_to_uuid5(control_id: ControlId) -> str:
    """Deterministically derive an OSCAL UUID from a CRML ControlId.

    Rationale:
    - OSCAL prefers UUIDs for stable cross-document linking.
    - CRML's canonical join key is ControlId (namespace:key).

    Using uuid5 ensures:
    - stable output across runs,
    - no randomness (good diffs),
    - reversible traceability (you can always store the original ControlId).
    """

    return str(uuid.uuid5(_CRML_OSCAL_NAMESPACE, str(control_id)))
