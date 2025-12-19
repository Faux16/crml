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
    CRPortfolioBundle,
    CRControlCatalog,
    CRAttackCatalog,
    CRAssessment,
    CRControlRelationships,
    CRAttackControlRelationships,
    CRSimulationResult,
    load_from_yaml,
    load_from_yaml_str,
    dump_to_yaml,
    dump_to_yaml_str,
)
from .validators import (
    ValidationMessage,
    ValidationReport,
    validate,
    validate_document,
    validate_portfolio,
    validate_assessment,
    validate_control_catalog,
    validate_attack_catalog,
    validate_control_relationships,
    validate_attack_control_relationships,
)

from .bundling import BundleReport, bundle_portfolio

__all__ = [
    "CRScenario",
    "CRPortfolio",
    "CRPortfolioBundle",
    "CRControlCatalog",
    "CRAttackCatalog",
    "CRAssessment",
    "CRControlRelationships",
    "CRAttackControlRelationships",
    "CRSimulationResult",
    "load_from_yaml",
    "load_from_yaml_str",
    "dump_to_yaml",
    "dump_to_yaml_str",
    "validate",
    "validate_document",
    "validate_portfolio",
    "validate_assessment",
    "validate_control_catalog",
    "validate_attack_catalog",
    "validate_control_relationships",
    "validate_attack_control_relationships",
    "bundle_portfolio",
    "BundleReport",
    "ValidationMessage",
    "ValidationReport",
]
