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

from typing import Any, Mapping, Union

import importlib

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


def _model_load_from_yaml(cls, path: str):
    data = load_yaml_mapping_from_path(path)
    return cls.model_validate(data)


def _model_load_from_yaml_str(cls, yaml_text: str):
    data = load_yaml_mapping_from_str(yaml_text)
    return cls.model_validate(data)


def _model_dump_to_yaml(
    model: Any,
    path: str,
    *,
    sort_keys: bool,
    exclude_none: bool,
    postprocess: Any = None,
) -> None:
    data = model.model_dump(by_alias=True, exclude_none=exclude_none)
    if postprocess is not None:
        postprocess(data)
    dump_yaml_to_path(data, path, sort_keys=sort_keys)


def _model_dump_to_yaml_str(
    model: Any,
    *,
    sort_keys: bool,
    exclude_none: bool,
    postprocess: Any = None,
) -> str:
    data = model.model_dump(by_alias=True, exclude_none=exclude_none)
    if postprocess is not None:
        postprocess(data)
    return dump_yaml_to_str(data, sort_keys=sort_keys)


def _drop_empty_portfolio_bundle_warnings(data: dict[str, Any]) -> None:
    """Remove `portfolio_bundle.warnings` if it is an empty list.

    This keeps bundle YAML concise while still allowing warnings to be present
    when they exist. The field remains optional during validation.
    """

    payload = data.get("portfolio_bundle")
    if not isinstance(payload, dict):
        return

    warnings = payload.get("warnings")
    if isinstance(warnings, list) and len(warnings) == 0:
        payload.pop("warnings", None)


class CRScenario(_CRScenario):
    """Root CRML Scenario document model.

    This is a small subclass of the internal Pydantic model that adds
    convenience constructors for YAML.
    """

    @classmethod
    def load_from_yaml(cls, path: str) -> "CRScenario":
        return _model_load_from_yaml(cls, path)

    @classmethod
    def load_from_yaml_str(cls, yaml_text: str) -> "CRScenario":
        return _model_load_from_yaml_str(cls, yaml_text)

    def dump_to_yaml(self, path: str, *, sort_keys: bool = False, exclude_none: bool = True) -> None:
        """Serialize this model to a YAML file at `path`."""
        _model_dump_to_yaml(self, path, sort_keys=sort_keys, exclude_none=exclude_none)

    def dump_to_yaml_str(self, *, sort_keys: bool = False, exclude_none: bool = True) -> str:
        """Serialize this model to a YAML string."""
        return _model_dump_to_yaml_str(self, sort_keys=sort_keys, exclude_none=exclude_none)

class CRPortfolioBundle(_CRPortfolioBundle):
    """Engine-agnostic portfolio bundle.

    The bundle model (schema/contract) is defined in `crml_lang`.
    Deterministic creation of bundles from portfolios is implemented in `crml_lang` (see `bundle_portfolio`).

    The engine consumes bundles by building an execution plan from them (see `crml_engine.pipeline.plan_bundle`).
    """

    @classmethod
    def load_from_yaml(cls, path: str) -> "CRPortfolioBundle":
        return _model_load_from_yaml(cls, path)

    @classmethod
    def load_from_yaml_str(cls, yaml_text: str) -> "CRPortfolioBundle":
        return _model_load_from_yaml_str(cls, yaml_text)

    def dump_to_yaml(self, path: str, *, sort_keys: bool = False, exclude_none: bool = True) -> None:
        """Serialize this model to a YAML file at `path`."""
        _model_dump_to_yaml(
            self,
            path,
            sort_keys=sort_keys,
            exclude_none=exclude_none,
            postprocess=_drop_empty_portfolio_bundle_warnings,
        )

    def dump_to_yaml_str(self, *, sort_keys: bool = False, exclude_none: bool = True) -> str:
        """Serialize this model to a YAML string."""
        return _model_dump_to_yaml_str(
            self,
            sort_keys=sort_keys,
            exclude_none=exclude_none,
            postprocess=_drop_empty_portfolio_bundle_warnings,
        )

def load_from_yaml(path: str) -> CRScenario:
    """Load a CRML scenario from a YAML file path."""
    return CRScenario.load_from_yaml(path)


def load_from_yaml_str(yaml_text: str) -> CRScenario:
    """Load a CRML scenario from a YAML string."""
    return CRScenario.load_from_yaml_str(yaml_text)


def dump_to_yaml(model: Union[CRScenario, Mapping[str, Any]], path: str, *, sort_keys: bool = False, exclude_none: bool = True) -> None:
    """Serialize a scenario model (or mapping) to a YAML file."""
    if isinstance(model, CRScenario):
        model.dump_to_yaml(path, sort_keys=sort_keys, exclude_none=exclude_none)
        return

    dump_yaml_to_path(dict(model), path, sort_keys=sort_keys)


def dump_to_yaml_str(model: Union[CRScenario, Mapping[str, Any]], *, sort_keys: bool = False, exclude_none: bool = True) -> str:
    """Serialize a scenario model (or mapping) to a YAML string."""
    if isinstance(model, CRScenario):
        return model.dump_to_yaml_str(sort_keys=sort_keys, exclude_none=exclude_none)

    return dump_yaml_to_str(dict(model), sort_keys=sort_keys)


class CRPortfolio(_CRPortfolio):
    """Root CRML Portfolio document model."""

    @classmethod
    def load_from_yaml(cls, path: str) -> "CRPortfolio":
        return _model_load_from_yaml(cls, path)

    @classmethod
    def load_from_yaml_str(cls, yaml_text: str) -> "CRPortfolio":
        return _model_load_from_yaml_str(cls, yaml_text)

    def dump_to_yaml(self, path: str, *, sort_keys: bool = False, exclude_none: bool = True) -> None:
        _model_dump_to_yaml(self, path, sort_keys=sort_keys, exclude_none=exclude_none)

    def dump_to_yaml_str(self, *, sort_keys: bool = False, exclude_none: bool = True) -> str:
        return _model_dump_to_yaml_str(self, sort_keys=sort_keys, exclude_none=exclude_none)


class CRControlCatalog(_CRControlCatalog):
    """Root CRML Control Catalog document model."""

    @classmethod
    def load_from_yaml(cls, path: str) -> "CRControlCatalog":
        return _model_load_from_yaml(cls, path)

    @classmethod
    def load_from_yaml_str(cls, yaml_text: str) -> "CRControlCatalog":
        return _model_load_from_yaml_str(cls, yaml_text)

    def dump_to_yaml(self, path: str, *, sort_keys: bool = False, exclude_none: bool = True) -> None:
        """Serialize this CRML model to a CRML YAML file at `path`."""
        _model_dump_to_yaml(self, path, sort_keys=sort_keys, exclude_none=exclude_none)

    def dump_to_yaml_str(self, *, sort_keys: bool = False, exclude_none: bool = True) -> str:
        """Serialize this CRML model to a CRML YAML string."""
        return _model_dump_to_yaml_str(self, sort_keys=sort_keys, exclude_none=exclude_none)

    @classmethod
    def fromOscal(
        cls,
        path: str,
        catalog_id: str | None = None,
        meta_name: str | None = None,
        source_url: str | None = None,
        license_terms: str | None = None,
    ) -> "CRControlCatalog":
        """Create a CRML Control Catalog from an OSCAL Catalog file (JSON/YAML).

        Notes:
        - This method returns a CRML model.
        - Use `dump_to_yaml()` to write CRML YAML.
        """

        # Dependency is declared by crml-lang, but we intentionally only import the
        # package root here because older oscal-pydantic releases are not fully
        # Pydantic-v2 compatible.
        importlib.import_module("oscal_pydantic")

        from crml_lang.oscal.convert import (
            infer_namespace_and_framework,
            oscal_catalog_to_crml_control_catalog,
        )
        from crml_lang.oscal.io import load_oscal_document

        oscal_doc = load_oscal_document(path=path)
        namespace, framework = infer_namespace_and_framework(oscal_doc)
        payload = oscal_catalog_to_crml_control_catalog(
            oscal_doc,
            namespace=namespace,
            framework=framework,
            catalog_id=catalog_id,
            meta_name=meta_name,
            source_url=source_url,
            license_terms=license_terms,
        )
        return cls.model_validate(payload)


class CRAttackCatalog(_CRAttackCatalog):
    """Root CRML Attack Catalog document model."""

    @classmethod
    def load_from_yaml(cls, path: str) -> "CRAttackCatalog":
        return _model_load_from_yaml(cls, path)

    @classmethod
    def load_from_yaml_str(cls, yaml_text: str) -> "CRAttackCatalog":
        return _model_load_from_yaml_str(cls, yaml_text)

    def dump_to_yaml(self, path: str, *, sort_keys: bool = False, exclude_none: bool = True) -> None:
        _model_dump_to_yaml(self, path, sort_keys=sort_keys, exclude_none=exclude_none)

    def dump_to_yaml_str(self, *, sort_keys: bool = False, exclude_none: bool = True) -> str:
        return _model_dump_to_yaml_str(self, sort_keys=sort_keys, exclude_none=exclude_none)


class CRAssessment(_CRAssessment):
    """Root CRML Assessment document model."""

    @classmethod
    def load_from_yaml(cls, path: str) -> "CRAssessment":
        return _model_load_from_yaml(cls, path)

    @classmethod
    def load_from_yaml_str(cls, yaml_text: str) -> "CRAssessment":
        return _model_load_from_yaml_str(cls, yaml_text)

    def dump_to_yaml(self, path: str, *, sort_keys: bool = False, exclude_none: bool = True) -> None:
        """Serialize this CRML model to a CRML YAML file at `path`."""
        _model_dump_to_yaml(self, path, sort_keys=sort_keys, exclude_none=exclude_none)

    def dump_to_yaml_str(self, *, sort_keys: bool = False, exclude_none: bool = True) -> str:
        """Serialize this CRML model to a CRML YAML string."""
        return _model_dump_to_yaml_str(self, sort_keys=sort_keys, exclude_none=exclude_none)

    @classmethod
    def fromOscal(
        cls,
        path: str,
        assessment_id: str | None = None,
        meta_name: str | None = None,
        source_url: str | None = None,
        license_terms: str | None = None,
        default_scf_cmm_level: int = 0,
    ) -> "CRAssessment":
        """Create a CRML Assessment template from an OSCAL Catalog file (JSON/YAML).

        Notes:
        - This method returns a CRML model.
        - Use `dump_to_yaml()` to write CRML YAML.
        """

        importlib.import_module("oscal_pydantic")

        from crml_lang.oscal.convert import (
            infer_namespace_and_framework,
            oscal_catalog_to_crml_assessment,
        )
        from crml_lang.oscal.io import load_oscal_document

        oscal_doc = load_oscal_document(path=path)
        namespace, framework = infer_namespace_and_framework(oscal_doc)
        payload = oscal_catalog_to_crml_assessment(
            oscal_doc,
            namespace=namespace,
            framework=framework,
            assessment_id=assessment_id,
            meta_name=meta_name,
            source_url=source_url,
            license_terms=license_terms,
            default_scf_cmm_level=default_scf_cmm_level,
        )
        return cls.model_validate(payload)


class CRControlRelationships(_CRControlRelationships):
    """Root CRML Control Relationships document model."""

    @classmethod
    def load_from_yaml(cls, path: str) -> "CRControlRelationships":
        return _model_load_from_yaml(cls, path)

    @classmethod
    def load_from_yaml_str(cls, yaml_text: str) -> "CRControlRelationships":
        return _model_load_from_yaml_str(cls, yaml_text)

    def dump_to_yaml(self, path: str, *, sort_keys: bool = False, exclude_none: bool = True) -> None:
        _model_dump_to_yaml(self, path, sort_keys=sort_keys, exclude_none=exclude_none)

    def dump_to_yaml_str(self, *, sort_keys: bool = False, exclude_none: bool = True) -> str:
        return _model_dump_to_yaml_str(self, sort_keys=sort_keys, exclude_none=exclude_none)


class CRAttackControlRelationships(_CRAttackControlRelationships):
    """Root CRML Attack-to-Control Relationships document model."""

    @classmethod
    def load_from_yaml(cls, path: str) -> "CRAttackControlRelationships":
        return _model_load_from_yaml(cls, path)

    @classmethod
    def load_from_yaml_str(cls, yaml_text: str) -> "CRAttackControlRelationships":
        return _model_load_from_yaml_str(cls, yaml_text)

    def dump_to_yaml(self, path: str, *, sort_keys: bool = False, exclude_none: bool = True) -> None:
        _model_dump_to_yaml(self, path, sort_keys=sort_keys, exclude_none=exclude_none)

    def dump_to_yaml_str(self, *, sort_keys: bool = False, exclude_none: bool = True) -> str:
        return _model_dump_to_yaml_str(self, sort_keys=sort_keys, exclude_none=exclude_none)

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
