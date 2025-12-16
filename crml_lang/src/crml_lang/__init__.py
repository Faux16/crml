"""Language/spec package for CRML.

This package contains:
- Pydantic models that represent the CRML document structure
- The CRML JSON Schema and a structured validator
- YAML load/dump helpers via `CRModel`

The reference runtime/simulation lives in the separate `crml_engine` package.
"""

from .api import (
    CRScenario,
    CRPortfolio,
    CRControlCatalog,
    CRControlAssessment,
    load_from_yaml,
    load_from_yaml_str,
    dump_to_yaml,
    dump_to_yaml_str,
)
from .validators import (
    ValidationMessage,
    ValidationReport,
    validate,
    validate_portfolio,
    validate_control_assessment,
    validate_control_catalog,
)

__all__ = [
    "CRScenario",
    "CRPortfolio",
    "CRControlCatalog",
    "CRControlAssessment",
    "load_from_yaml",
    "load_from_yaml_str",
    "dump_to_yaml",
    "dump_to_yaml_str",
    "validate",
    "validate_portfolio",
    "validate_control_assessment",
    "validate_control_catalog",
    "ValidationMessage",
    "ValidationReport",
]
