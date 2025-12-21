"""OSCAL conversion helpers.

This package provides conversions from OSCAL JSON/YAML documents into CRML models.

Field mapping review:
- See `field-mappings.yaml` for the intended OSCAL -> CRML field mapping rules.
"""

from .config import OscalEndpoint, load_endpoints
from .convert import (
    oscal_catalog_to_crml_assessment,
    oscal_catalog_to_crml_control_catalog,
)
from .errors import (
    OscalConvertError,
    OscalEndpointNotFoundError,
    OscalError,
    OscalFetchError,
    OscalParseError,
)
from .helpers import (
    assessment_template_from_endpoint,
    control_catalog_from_endpoint,
    get_endpoint,
    list_endpoints,
    load_oscal_from_endpoint,
)
from .io import load_oscal_document
from .provenance import OscalProvenance

__all__ = [
    "OscalEndpoint",
    "load_endpoints",
    "get_endpoint",
    "list_endpoints",
    "load_oscal_from_endpoint",
    "control_catalog_from_endpoint",
    "assessment_template_from_endpoint",
    "load_oscal_document",
    "oscal_catalog_to_crml_control_catalog",
    "oscal_catalog_to_crml_assessment",
    "OscalProvenance",
    "OscalError",
    "OscalEndpointNotFoundError",
    "OscalFetchError",
    "OscalParseError",
    "OscalConvertError",
]
