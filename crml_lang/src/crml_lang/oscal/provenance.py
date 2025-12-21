from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True, slots=True)
class OscalProvenance:
    """Provenance metadata for an OSCAL ingest operation."""

    source_kind: str  # path|url|endpoint
    source: str
    endpoint_id: Optional[str] = None
    fetched_at_utc: Optional[str] = None

    @staticmethod
    def now_utc_iso() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
