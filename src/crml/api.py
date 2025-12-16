"""Public, stable Python API for crml-lang.

This module is intended as the supported import surface for downstream users.
Internal modules may change structure over time; symbols exported here should
remain stable.
"""

from __future__ import annotations

from typing import Any, Mapping

from .models.crml_model import CRMLSchema as _CRMLSchema
from .validator import validate_crml as validate


class CRModel(_CRMLSchema):
    """Root CRML document model.

    This is a small subclass of the internal Pydantic model that adds
    convenience constructors for YAML.
    """

    @classmethod
    def load_from_yaml(cls, path: str) -> "CRModel":
        try:
            import yaml
        except Exception as e:
            raise ImportError("PyYAML is required to load YAML files: pip install pyyaml") from e

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data)

    @classmethod
    def load_from_yaml_str(cls, yaml_text: str) -> "CRModel":
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


def load_from_yaml(path: str) -> CRModel:
    return CRModel.load_from_yaml(path)


def load_from_yaml_str(yaml_text: str) -> CRModel:
    return CRModel.load_from_yaml_str(yaml_text)


def dump_to_yaml(model: CRModel | Mapping[str, Any], path: str, *, sort_keys: bool = False, exclude_none: bool = True) -> None:
    if isinstance(model, CRModel):
        model.dump_to_yaml(path, sort_keys=sort_keys, exclude_none=exclude_none)
        return

    try:
        import yaml
    except Exception as e:
        raise ImportError("PyYAML is required to write YAML files: pip install pyyaml") from e

    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(dict(model), f, sort_keys=sort_keys, allow_unicode=True)


def dump_to_yaml_str(model: CRModel | Mapping[str, Any], *, sort_keys: bool = False, exclude_none: bool = True) -> str:
    if isinstance(model, CRModel):
        return model.dump_to_yaml_str(sort_keys=sort_keys, exclude_none=exclude_none)

    try:
        import yaml
    except Exception as e:
        raise ImportError("PyYAML is required to write YAML: pip install pyyaml") from e

    return yaml.safe_dump(dict(model), sort_keys=sort_keys, allow_unicode=True)

__all__ = [
    "CRModel",
    "load_from_yaml",
    "load_from_yaml_str",
    "dump_to_yaml",
    "dump_to_yaml_str",
    "validate",
]
