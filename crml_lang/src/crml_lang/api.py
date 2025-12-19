"""Public, stable Python API for crml-lang.

This module is intended as the supported import surface for downstream users.
Internal modules may change structure over time; symbols exported here should
remain stable.

Usage examples
--------------

Load a scenario from YAML::

    from crml_lang import CRScenario

    scenario = CRScenario.load_from_yaml("scenario.yaml")
    # or: scenario = CRScenario.load_from_yaml_str(yaml_text)

Dump a scenario back to YAML::

    yaml_text = scenario.dump_to_yaml_str()
    scenario.dump_to_yaml("out.yaml")

Validate a scenario document (schema + semantic warnings)::

    from crml_lang import validate

    report = validate("scenario.yaml", source_kind="path")
    if not report.ok:
        print(report.render_text(source_label="scenario.yaml"))
"""

from __future__ import annotations

from typing import Any, Mapping

from .yamlio import (
    dump_yaml_to_path,
    dump_yaml_to_str,
    load_yaml_mapping_from_path,
    load_yaml_mapping_from_str,
)

from .models.scenario_model import CRScenario as _CRScenario
from .models.assessment_model import CRAssessment as _CRAssessment
from .models.control_catalog_model import CRControlCatalog as _CRControlCatalog
from .models.attack_catalog_model import CRAttackCatalog as _CRAttackCatalog
from .models.attack_control_relationships_model import (
    CRAttackControlRelationships as _CRAttackControlRelationships,
)
from .models.control_relationships_model import CRControlRelationships as _CRControlRelationships
from .models.portfolio_model import CRPortfolio as _CRPortfolio
from .models.portfolio_bundle import CRPortfolioBundle as _CRPortfolioBundle
from .models.simulation_result import CRSimulationResult
from .validators import ValidationMessage, ValidationReport, validate, validate_portfolio
from .validators import validate_attack_catalog
from .validators import validate_attack_control_relationships


class CRScenario(_CRScenario):
    """Root CRML Scenario document model.

    This is a small subclass of the internal Pydantic model that adds
    convenience constructors for YAML.
    """

    @classmethod
    def load_from_yaml(cls, path: str) -> "CRScenario":
        data = load_yaml_mapping_from_path(path)
        return cls.model_validate(data)

    @classmethod
    def load_from_yaml_str(cls, yaml_text: str) -> "CRScenario":
        data = load_yaml_mapping_from_str(yaml_text)
        return cls.model_validate(data)

    def dump_to_yaml(self, path: str, *, sort_keys: bool = False, exclude_none: bool = True) -> None:
        """Serialize this model to a YAML file at `path`."""
        data = self.model_dump(by_alias=True, exclude_none=exclude_none)
        dump_yaml_to_path(data, path, sort_keys=sort_keys)

    def dump_to_yaml_str(self, *, sort_keys: bool = False, exclude_none: bool = True) -> str:
        """Serialize this model to a YAML string."""
        data = self.model_dump(by_alias=True, exclude_none=exclude_none)
        return dump_yaml_to_str(data, sort_keys=sort_keys)

class CRPortfolioBundle(_CRPortfolioBundle):
    """Engine-agnostic portfolio bundle.

    The bundle model (schema/contract) is defined in `crml_lang`.
    Deterministic creation of bundles from portfolios is implemented in `crml_lang` (see `bundle_portfolio`).

    The engine consumes bundles by building an execution plan from them (see `crml_engine.pipeline.plan_bundle`).
    """

    @classmethod
    def load_from_yaml(cls, path: str) -> "CRPortfolioBundle":
        data = load_yaml_mapping_from_path(path)
        return cls.model_validate(data)

    @classmethod
    def load_from_yaml_str(cls, yaml_text: str) -> "CRPortfolioBundle":
        data = load_yaml_mapping_from_str(yaml_text)
        return cls.model_validate(data)

    def dump_to_yaml(self, path: str, *, sort_keys: bool = False, exclude_none: bool = True) -> None:
        """Serialize this model to a YAML file at `path`."""
        data = self.model_dump(by_alias=True, exclude_none=exclude_none)
        dump_yaml_to_path(data, path, sort_keys=sort_keys)

    def dump_to_yaml_str(self, *, sort_keys: bool = False, exclude_none: bool = True) -> str:
        """Serialize this model to a YAML string."""
        data = self.model_dump(by_alias=True, exclude_none=exclude_none)
        return dump_yaml_to_str(data, sort_keys=sort_keys)

def load_from_yaml(path: str) -> CRScenario:
    """Load a CRML scenario from a YAML file path."""
    return CRScenario.load_from_yaml(path)


def load_from_yaml_str(yaml_text: str) -> CRScenario:
    """Load a CRML scenario from a YAML string."""
    return CRScenario.load_from_yaml_str(yaml_text)


def dump_to_yaml(model: CRScenario | Mapping[str, Any], path: str, *, sort_keys: bool = False, exclude_none: bool = True) -> None:
    """Serialize a scenario model (or mapping) to a YAML file."""
    if isinstance(model, CRScenario):
        model.dump_to_yaml(path, sort_keys=sort_keys, exclude_none=exclude_none)
        return

    dump_yaml_to_path(dict(model), path, sort_keys=sort_keys)


def dump_to_yaml_str(model: CRScenario | Mapping[str, Any], *, sort_keys: bool = False, exclude_none: bool = True) -> str:
    """Serialize a scenario model (or mapping) to a YAML string."""
    if isinstance(model, CRScenario):
        return model.dump_to_yaml_str(sort_keys=sort_keys, exclude_none=exclude_none)

    return dump_yaml_to_str(dict(model), sort_keys=sort_keys)


class CRPortfolio(_CRPortfolio):
    """Root CRML Portfolio document model."""

    @classmethod
    def load_from_yaml(cls, path: str) -> "CRPortfolio":
        data = load_yaml_mapping_from_path(path)
        return cls.model_validate(data)

    @classmethod
    def load_from_yaml_str(cls, yaml_text: str) -> "CRPortfolio":
        data = load_yaml_mapping_from_str(yaml_text)
        return cls.model_validate(data)

    def dump_to_yaml(self, path: str, *, sort_keys: bool = False, exclude_none: bool = True) -> None:
        data = self.model_dump(by_alias=True, exclude_none=exclude_none)
        dump_yaml_to_path(data, path, sort_keys=sort_keys)

    def dump_to_yaml_str(self, *, sort_keys: bool = False, exclude_none: bool = True) -> str:
        data = self.model_dump(by_alias=True, exclude_none=exclude_none)
        return dump_yaml_to_str(data, sort_keys=sort_keys)


class CRControlCatalog(_CRControlCatalog):
    """Root CRML Control Catalog document model."""

    @classmethod
    def load_from_yaml(cls, path: str) -> "CRControlCatalog":
        data = load_yaml_mapping_from_path(path)
        return cls.model_validate(data)

    @classmethod
    def load_from_yaml_str(cls, yaml_text: str) -> "CRControlCatalog":
        data = load_yaml_mapping_from_str(yaml_text)
        return cls.model_validate(data)

    def dump_to_yaml(self, path: str, *, sort_keys: bool = False, exclude_none: bool = True) -> None:
        data = self.model_dump(by_alias=True, exclude_none=exclude_none)
        dump_yaml_to_path(data, path, sort_keys=sort_keys)

    def dump_to_yaml_str(self, *, sort_keys: bool = False, exclude_none: bool = True) -> str:
        data = self.model_dump(by_alias=True, exclude_none=exclude_none)
        return dump_yaml_to_str(data, sort_keys=sort_keys)


class CRAttackCatalog(_CRAttackCatalog):
    """Root CRML Attack Catalog document model."""

    @classmethod
    def load_from_yaml(cls, path: str) -> "CRAttackCatalog":
        data = load_yaml_mapping_from_path(path)
        return cls.model_validate(data)

    @classmethod
    def load_from_yaml_str(cls, yaml_text: str) -> "CRAttackCatalog":
        data = load_yaml_mapping_from_str(yaml_text)
        return cls.model_validate(data)

    def dump_to_yaml(self, path: str, *, sort_keys: bool = False, exclude_none: bool = True) -> None:
        data = self.model_dump(by_alias=True, exclude_none=exclude_none)
        dump_yaml_to_path(data, path, sort_keys=sort_keys)

    def dump_to_yaml_str(self, *, sort_keys: bool = False, exclude_none: bool = True) -> str:
        data = self.model_dump(by_alias=True, exclude_none=exclude_none)
        return dump_yaml_to_str(data, sort_keys=sort_keys)


class CRAssessment(_CRAssessment):
    """Root CRML Assessment document model."""

    @classmethod
    def load_from_yaml(cls, path: str) -> "CRAssessment":
        data = load_yaml_mapping_from_path(path)
        return cls.model_validate(data)

    @classmethod
    def load_from_yaml_str(cls, yaml_text: str) -> "CRAssessment":
        data = load_yaml_mapping_from_str(yaml_text)
        return cls.model_validate(data)

    def dump_to_yaml(self, path: str, *, sort_keys: bool = False, exclude_none: bool = True) -> None:
        data = self.model_dump(by_alias=True, exclude_none=exclude_none)
        dump_yaml_to_path(data, path, sort_keys=sort_keys)

    def dump_to_yaml_str(self, *, sort_keys: bool = False, exclude_none: bool = True) -> str:
        data = self.model_dump(by_alias=True, exclude_none=exclude_none)
        return dump_yaml_to_str(data, sort_keys=sort_keys)


class CRControlRelationships(_CRControlRelationships):
    """Root CRML Control Relationships document model."""

    @classmethod
    def load_from_yaml(cls, path: str) -> "CRControlRelationships":
        data = load_yaml_mapping_from_path(path)
        return cls.model_validate(data)

    @classmethod
    def load_from_yaml_str(cls, yaml_text: str) -> "CRControlRelationships":
        data = load_yaml_mapping_from_str(yaml_text)
        return cls.model_validate(data)

    def dump_to_yaml(self, path: str, *, sort_keys: bool = False, exclude_none: bool = True) -> None:
        data = self.model_dump(by_alias=True, exclude_none=exclude_none)
        dump_yaml_to_path(data, path, sort_keys=sort_keys)

    def dump_to_yaml_str(self, *, sort_keys: bool = False, exclude_none: bool = True) -> str:
        data = self.model_dump(by_alias=True, exclude_none=exclude_none)
        return dump_yaml_to_str(data, sort_keys=sort_keys)


class CRAttackControlRelationships(_CRAttackControlRelationships):
    """Root CRML Attack-to-Control Relationships document model."""

    @classmethod
    def load_from_yaml(cls, path: str) -> "CRAttackControlRelationships":
        data = load_yaml_mapping_from_path(path)
        return cls.model_validate(data)

    @classmethod
    def load_from_yaml_str(cls, yaml_text: str) -> "CRAttackControlRelationships":
        data = load_yaml_mapping_from_str(yaml_text)
        return cls.model_validate(data)

    def dump_to_yaml(self, path: str, *, sort_keys: bool = False, exclude_none: bool = True) -> None:
        data = self.model_dump(by_alias=True, exclude_none=exclude_none)
        dump_yaml_to_path(data, path, sort_keys=sort_keys)

    def dump_to_yaml_str(self, *, sort_keys: bool = False, exclude_none: bool = True) -> str:
        data = self.model_dump(by_alias=True, exclude_none=exclude_none)
        return dump_yaml_to_str(data, sort_keys=sort_keys)

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
    "validate_portfolio",
    "validate_attack_catalog",
    "validate_attack_control_relationships",
    "ValidationMessage",
    "ValidationReport",
]
