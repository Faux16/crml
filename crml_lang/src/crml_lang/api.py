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

from .models.crml_model import CRScenarioSchema as _CRScenarioSchema
from .models.control_assessment_model import CRControlAssessmentSchema as _CRControlAssessmentSchema
from .models.control_catalog_model import CRControlCatalogSchema as _CRControlCatalogSchema
from .models.portfolio_model import CRPortfolioSchema as _CRPortfolioSchema
from .validator import ValidationMessage, ValidationReport, validate, validate_portfolio


class CRScenario(_CRScenarioSchema):
    """Root CRML Scenario document model.

    This is a small subclass of the internal Pydantic model that adds
    convenience constructors for YAML.
    """

    @classmethod
    def load_from_yaml(cls, path: str) -> "CRScenario":
        try:
            import yaml
        except Exception as e:
            raise ImportError("PyYAML is required to load YAML files: pip install pyyaml") from e

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data)

    @classmethod
    def load_from_yaml_str(cls, yaml_text: str) -> "CRScenario":
        try:
            import yaml
        except Exception as e:
            raise ImportError("PyYAML is required to load YAML strings: pip install pyyaml") from e

        data = yaml.safe_load(yaml_text)
        return cls.model_validate(data)

    def dump_to_yaml(self, path: str, *, sort_keys: bool = False, exclude_none: bool = True) -> None:
        """Serialize this model to a YAML file at `path`."""
        try:
            import yaml
        except Exception as e:
            raise ImportError("PyYAML is required to write YAML files: pip install pyyaml") from e

        data = self.model_dump(by_alias=True, exclude_none=exclude_none)
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=sort_keys, allow_unicode=True)

    def dump_to_yaml_str(self, *, sort_keys: bool = False, exclude_none: bool = True) -> str:
        """Serialize this model to a YAML string."""
        try:
            import yaml
        except Exception as e:
            raise ImportError("PyYAML is required to write YAML: pip install pyyaml") from e

        data = self.model_dump(by_alias=True, exclude_none=exclude_none)
        return yaml.safe_dump(data, sort_keys=sort_keys, allow_unicode=True)


def load_from_yaml(path: str) -> CRScenario:
    return CRScenario.load_from_yaml(path)


def load_from_yaml_str(yaml_text: str) -> CRScenario:
    return CRScenario.load_from_yaml_str(yaml_text)


def dump_to_yaml(model: CRScenario | Mapping[str, Any], path: str, *, sort_keys: bool = False, exclude_none: bool = True) -> None:
    if isinstance(model, CRScenario):
        model.dump_to_yaml(path, sort_keys=sort_keys, exclude_none=exclude_none)
        return

    try:
        import yaml
    except Exception as e:
        raise ImportError("PyYAML is required to write YAML files: pip install pyyaml") from e

    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(dict(model), f, sort_keys=sort_keys, allow_unicode=True)


def dump_to_yaml_str(model: CRScenario | Mapping[str, Any], *, sort_keys: bool = False, exclude_none: bool = True) -> str:
    if isinstance(model, CRScenario):
        return model.dump_to_yaml_str(sort_keys=sort_keys, exclude_none=exclude_none)

    try:
        import yaml
    except Exception as e:
        raise ImportError("PyYAML is required to write YAML: pip install pyyaml") from e

    return yaml.safe_dump(dict(model), sort_keys=sort_keys, allow_unicode=True)


class CRPortfolio(_CRPortfolioSchema):
    """Root CRML Portfolio document model."""

    @classmethod
    def load_from_yaml(cls, path: str) -> "CRPortfolio":
        try:
            import yaml
        except Exception as e:
            raise ImportError("PyYAML is required to load YAML files: pip install pyyaml") from e

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data)

    @classmethod
    def load_from_yaml_str(cls, yaml_text: str) -> "CRPortfolio":
        try:
            import yaml
        except Exception as e:
            raise ImportError("PyYAML is required to load YAML strings: pip install pyyaml") from e

        data = yaml.safe_load(yaml_text)
        return cls.model_validate(data)

    def dump_to_yaml(self, path: str, *, sort_keys: bool = False, exclude_none: bool = True) -> None:
        try:
            import yaml
        except Exception as e:
            raise ImportError("PyYAML is required to write YAML files: pip install pyyaml") from e

        data = self.model_dump(by_alias=True, exclude_none=exclude_none)
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=sort_keys, allow_unicode=True)

    def dump_to_yaml_str(self, *, sort_keys: bool = False, exclude_none: bool = True) -> str:
        try:
            import yaml
        except Exception as e:
            raise ImportError("PyYAML is required to write YAML: pip install pyyaml") from e

        data = self.model_dump(by_alias=True, exclude_none=exclude_none)
        return yaml.safe_dump(data, sort_keys=sort_keys, allow_unicode=True)


class CRControlCatalog(_CRControlCatalogSchema):
    """Root CRML Control Catalog document model."""

    @classmethod
    def load_from_yaml(cls, path: str) -> "CRControlCatalog":
        try:
            import yaml
        except Exception as e:
            raise ImportError("PyYAML is required to load YAML files: pip install pyyaml") from e

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data)

    @classmethod
    def load_from_yaml_str(cls, yaml_text: str) -> "CRControlCatalog":
        try:
            import yaml
        except Exception as e:
            raise ImportError("PyYAML is required to load YAML strings: pip install pyyaml") from e

        data = yaml.safe_load(yaml_text)
        return cls.model_validate(data)

    def dump_to_yaml(self, path: str, *, sort_keys: bool = False, exclude_none: bool = True) -> None:
        try:
            import yaml
        except Exception as e:
            raise ImportError("PyYAML is required to write YAML files: pip install pyyaml") from e

        data = self.model_dump(by_alias=True, exclude_none=exclude_none)
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=sort_keys, allow_unicode=True)

    def dump_to_yaml_str(self, *, sort_keys: bool = False, exclude_none: bool = True) -> str:
        try:
            import yaml
        except Exception as e:
            raise ImportError("PyYAML is required to write YAML: pip install pyyaml") from e

        data = self.model_dump(by_alias=True, exclude_none=exclude_none)
        return yaml.safe_dump(data, sort_keys=sort_keys, allow_unicode=True)


class CRControlAssessment(_CRControlAssessmentSchema):
    """Root CRML Control Assessment document model."""

    @classmethod
    def load_from_yaml(cls, path: str) -> "CRControlAssessment":
        try:
            import yaml
        except Exception as e:
            raise ImportError("PyYAML is required to load YAML files: pip install pyyaml") from e

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data)

    @classmethod
    def load_from_yaml_str(cls, yaml_text: str) -> "CRControlAssessment":
        try:
            import yaml
        except Exception as e:
            raise ImportError("PyYAML is required to load YAML strings: pip install pyyaml") from e

        data = yaml.safe_load(yaml_text)
        return cls.model_validate(data)

    def dump_to_yaml(self, path: str, *, sort_keys: bool = False, exclude_none: bool = True) -> None:
        try:
            import yaml
        except Exception as e:
            raise ImportError("PyYAML is required to write YAML files: pip install pyyaml") from e

        data = self.model_dump(by_alias=True, exclude_none=exclude_none)
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=sort_keys, allow_unicode=True)

    def dump_to_yaml_str(self, *, sort_keys: bool = False, exclude_none: bool = True) -> str:
        try:
            import yaml
        except Exception as e:
            raise ImportError("PyYAML is required to write YAML: pip install pyyaml") from e

        data = self.model_dump(by_alias=True, exclude_none=exclude_none)
        return yaml.safe_dump(data, sort_keys=sort_keys, allow_unicode=True)

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
    "ValidationMessage",
    "ValidationReport",
]
