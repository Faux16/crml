from __future__ import annotations

import os
import re
import tempfile
from typing import Any

import yaml


_YAML_AMBIGUOUS_PLAIN_SCALAR_RE = re.compile(
    r"^(?:"
    # YAML 1.1 booleans (PyYAML default resolver behavior)
    r"(?:y|Y|yes|Yes|YES|n|N|no|No|NO|true|True|TRUE|false|False|FALSE|on|On|ON|off|Off|OFF)"
    r"|(?:null|Null|NULL|~)"
    # Common numeric forms that YAML parsers will coerce
    r"|(?:[-+]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][-+]?[0-9]+)?)"
    r"|(?:0x[0-9a-fA-F_]+)"
    r"|(?:0o[0-7_]+)"
    r"|(?:0b[01_]+)"
    r")$"
)


class _CRMLSafeDumper(yaml.SafeDumper):
    """YAML dumper that avoids emitting ambiguous plain scalars.

    We intentionally quote strings like '1.0' so that re-loading the YAML does not
    change types (e.g., version headers becoming floats).
    """


def _represent_str(dumper: yaml.Dumper, data: str) -> yaml.nodes.ScalarNode:  # type: ignore[name-defined]
    if _YAML_AMBIGUOUS_PLAIN_SCALAR_RE.match(data):
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="'")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


_CRMLSafeDumper.add_representer(str, _represent_str)


_DOC_ROOT_KEY_ORDERS: list[tuple[str, list[str]]] = [
    # Keep CRML version + meta at the top for readability, even when keys are sorted.
    ("crml_control_catalog", ["crml_control_catalog", "meta", "catalog"]),
    ("crml_assessment", ["crml_assessment", "meta", "assessment"]),
    ("crml_portfolio_bundle", ["crml_portfolio_bundle", "meta", "bundle"]),
    ("crml_portfolio", ["crml_portfolio", "meta", "portfolio"]),
    ("crml_scenario", ["crml_scenario", "meta", "scenario"]),
    ("crml_simulation_result", ["crml_simulation_result", "meta", "result"]),
    ("crml_attack_catalog", ["crml_attack_catalog", "meta", "catalog"]),
    ("crml_control_relationships", ["crml_control_relationships", "meta", "relationships"]),
]


def _canonicalize_for_yaml(obj: Any, *, _depth: int = 0) -> Any:
    """Recursively canonicalize mappings for deterministic YAML output.

    Notes:
    - Only affects mapping key ordering (does not reorder lists).
    - At the document root, keeps CRML version + meta keys at the top.
    """

    if isinstance(obj, dict):
        preferred: list[str] | None = None
        if _depth == 0:
            for marker_key, order in _DOC_ROOT_KEY_ORDERS:
                if marker_key in obj:
                    preferred = order
                    break

        if preferred:
            preferred_keys = [k for k in preferred if k in obj]
            other_keys = sorted([k for k in obj.keys() if k not in preferred], key=lambda k: str(k))
            keys = preferred_keys + other_keys
        else:
            keys = sorted(obj.keys(), key=lambda k: str(k))

        out: dict[Any, Any] = {}
        for k in keys:
            out[k] = _canonicalize_for_yaml(obj[k], _depth=_depth + 1)
        return out

    if isinstance(obj, list):
        return [_canonicalize_for_yaml(v, _depth=_depth + 1) for v in obj]

    return obj


def load_yaml_mapping_from_str(text: str) -> dict[str, Any]:
    """Parse YAML text and require a mapping/object at the root."""
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
    if sort_keys:
        data = _canonicalize_for_yaml(data)
    return yaml.dump(
        data,
        # We pre-order mappings ourselves so CRML headers stay on top.
        sort_keys=False,
        allow_unicode=True,
        Dumper=_CRMLSafeDumper,
    )


def dump_yaml_to_path(data: Any, path: str, *, sort_keys: bool = False) -> None:
    """Serialize data to YAML at the given file path."""
    if sort_keys:
        data = _canonicalize_for_yaml(data)
    out_path = os.fspath(path)
    out_dir = os.path.dirname(out_path) or "."
    os.makedirs(out_dir, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(
        prefix=os.path.basename(out_path) + ".",
        suffix=".tmp",
        dir=out_dir,
        text=True,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            yaml.dump(
                data,
                f,
                # We pre-order mappings ourselves so CRML headers stay on top.
                sort_keys=False,
                allow_unicode=True,
                Dumper=_CRMLSafeDumper,
            )
            f.flush()
            os.fsync(f.fileno())

        os.replace(tmp_path, out_path)
    finally:
        try:
            os.remove(tmp_path)
        except FileNotFoundError:
            pass
