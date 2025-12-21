"""Schema-specific validation entrypoints.

This package splits CRML validation by document type:
- Scenario (`crml_scenario`)
- Portfolio (`crml_portfolio`)
- Control catalog packs (`crml_control_catalog`)
- Attack catalog packs (`crml_attack_catalog`)
- Assessment packs (`crml_assessment`)
- Control relationships packs (`crml_control_relationships`)
- Attack-to-control relationships mappings (`crml_attack_control_relationships`)
"""

from .common import ValidationMessage, ValidationReport
from .scenario import validate
from .document import validate_document
from .portfolio import validate_portfolio
from .control_catalog import validate_control_catalog
from .attack_catalog import validate_attack_catalog
from .attack_control_relationships import validate_attack_control_relationships
from .assessment import validate_assessment
from .control_relationships import validate_control_relationships

__all__ = [
    "ValidationMessage",
    "ValidationReport",
    "validate",
    "validate_document",
    "validate_portfolio",
    "validate_assessment",
    "validate_control_catalog",
    "validate_attack_catalog",
    "validate_attack_control_relationships",
    "validate_control_relationships",
]
