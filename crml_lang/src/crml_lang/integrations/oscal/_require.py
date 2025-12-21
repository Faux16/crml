from __future__ import annotations
import importlib


def require_oscal() -> None:
    """Ensure the optional OSCAL dependency is available.

    We use Compliance Trestle as the OSCAL Python model library.
    """

    try:
        importlib.import_module("trestle")
    except Exception as exc:  # pragma: no cover
        raise ImportError(
            "OSCAL support requires optional dependencies. "
            "Install with: pip install \"crml-lang[oscal]\""
        ) from exc
