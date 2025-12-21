"""OSCAL interoperability helpers.

This package is intentionally optional.

Install the optional dependency group:
  pip install "crml-lang[oscal]"

The conversion functions aim to be:
- minimal and predictable,
- safe with respect to copyrighted control text (CRML catalogs should remain metadata-only),
- compatible with CRML's canonical join key: ControlId (namespace:key).
"""

from ._require import require_oscal
from .ids import control_id_to_uuid5
from .catalog_ingest import (
  OscalCatalogProvenance,
  read_oscal_catalog,
  oscal_catalog_to_crml_control_catalog,
)

__all__ = [
    "require_oscal",
    "control_id_to_uuid5",
  "OscalCatalogProvenance",
  "read_oscal_catalog",
  "oscal_catalog_to_crml_control_catalog",
]
