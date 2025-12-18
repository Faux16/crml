from __future__ import annotations

from typing import Any


_ERR_PYYAML_REQUIRED = "PyYAML is required: pip install pyyaml"


def _yaml_module():
    """Import and return the PyYAML module.

    This is isolated to keep PyYAML as an modular dependency for the package.

    Raises:
        ImportError: If PyYAML is not installed.
    """
    try:
        import yaml  # type: ignore

        return yaml
    except Exception as e:  # pragma: no cover
        raise ImportError(_ERR_PYYAML_REQUIRED) from e


def load_yaml_mapping_from_str(text: str) -> dict[str, Any]:
    """Parse YAML text and require a mapping/object at the root."""

    yaml = _yaml_module()
    data = yaml.safe_load(text)

    if not isinstance(data, dict):
        raise ValueError("YAML document must be a mapping/object at top-level")

    return data


def load_yaml_mapping_from_path(path: str) -> dict[str, Any]:
    """Read YAML file and require a mapping/object at the root."""

    with open(path, "r", encoding="utf-8") as f:
        return load_yaml_mapping_from_str(f.read())


def dump_yaml_to_str(data: Any, *, sort_keys: bool = False) -> str:
    """Serialize data to YAML."""

    yaml = _yaml_module()
    return yaml.safe_dump(data, sort_keys=sort_keys, allow_unicode=True)


def dump_yaml_to_path(data: Any, path: str, *, sort_keys: bool = False) -> None:
    """Serialize data to YAML at the given file path."""

    yaml = _yaml_module()
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=sort_keys, allow_unicode=True)
