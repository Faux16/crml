"""Schema-specific validation entrypoints.

This package splits CRML validation by document type:
- Scenario (`crml_scenario`)
- Portfolio (`crml_portfolio`)
- Control catalog packs (`crml_control_catalog`)
- Control assessment packs (`crml_control_assessment`)
- Control relationships packs (`crml_control_relationships`)

The legacy module `crml_lang.validator` re-exports these APIs for backward
compatibility.
"""

from .common import ValidationMessage, ValidationReport
from .scenario import validate
from .document import validate_document
from .portfolio import validate_portfolio
from .control_catalog import validate_control_catalog
from .control_assessment import validate_control_assessment
from .control_relationships import validate_control_relationships

__all__ = [
    "ValidationMessage",
    "ValidationReport",
    "validate",
    "validate_document",
    "validate_portfolio",
    "validate_control_assessment",
    "validate_control_catalog",
    "validate_control_relationships",
]
