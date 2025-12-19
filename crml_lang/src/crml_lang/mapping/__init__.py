"""XLSX import/export for CRML data packs.

This module is intentionally small and strict:
- It writes a versioned workbook format (see `_meta` sheet).
- It round-trips without data loss for the supported CRML document types.

XLSX support is an optional dependency.
"""

from .xlsx import (
    import_xlsx,
    export_xlsx,
    ImportedXlsx,
    write_imported_as_yaml,
)

__all__ = [
    "export_xlsx",
    "import_xlsx",
    "ImportedXlsx",
    "write_imported_as_yaml",
]
