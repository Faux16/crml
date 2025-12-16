from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any, Literal, Optional


# Package root: .../crml_lang
_PACKAGE_DIR = Path(__file__).resolve().parents[1]
_SCHEMA_DIR = _PACKAGE_DIR / "schemas"

SCENARIO_SCHEMA_PATH = str(_SCHEMA_DIR / "crml-scenario-schema.json")
PORTFOLIO_SCHEMA_PATH = str(_SCHEMA_DIR / "crml-portfolio-schema.json")
CONTROL_ASSESSMENT_SCHEMA_PATH = str(_SCHEMA_DIR / "crml-control-assessment-schema.json")
CONTROL_CATALOG_SCHEMA_PATH = str(_SCHEMA_DIR / "crml-control-catalog-schema.json")


@dataclass(frozen=True)
class ValidationMessage:
    """A single validation message (error or warning)."""

    level: Literal["error", "warning"]
    message: str
    path: str = "(root)"
    source: Literal["schema", "semantic", "pydantic", "io"] = "schema"
    validator: Optional[str] = None


@dataclass(frozen=True)
class ValidationReport:
    """Structured validation output."""

    ok: bool
    errors: list[ValidationMessage]
    warnings: list[ValidationMessage]

    def render_text(self, *, source_label: Optional[str] = None) -> str:
        """Render a human-friendly validation summary (used by the CLI)."""

        label = source_label or "(input)"
        lines: list[str] = []

        if self.ok:
            lines.append(f"[OK] {label} is a valid CRML document.")
            for w in self.warnings:
                lines.append(f"[WARNING] {w.message}")
            return "\n".join(lines)

        lines.append(f"[ERROR] {label} failed CRML validation with {len(self.errors)} error(s):")
        for i, e in enumerate(self.errors, 1):
            lines.append(f"  {i}. [{e.path}] {e.message}")
        for w in self.warnings:
            lines.append(f"[WARNING] {w.message}")
        return "\n".join(lines)


def _load_schema(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_scenario_schema() -> dict[str, Any]:
    return _load_schema(SCENARIO_SCHEMA_PATH)


def _load_portfolio_schema() -> dict[str, Any]:
    return _load_schema(PORTFOLIO_SCHEMA_PATH)


def _load_control_assessment_schema() -> dict[str, Any]:
    return _load_schema(CONTROL_ASSESSMENT_SCHEMA_PATH)


def _load_control_catalog_schema() -> dict[str, Any]:
    return _load_schema(CONTROL_CATALOG_SCHEMA_PATH)


def _looks_like_yaml_text(s: str) -> bool:
    # Heuristic: YAML documents almost always contain either newlines or key separators.
    return "\n" in s or ":" in s


def _load_input(
    source: str | dict[str, Any],
    *,
    source_kind: Literal["path", "yaml", "data"] | None,
) -> tuple[Optional[dict[str, Any]], list[ValidationMessage]]:
    errors: list[ValidationMessage] = []

    if source_kind == "data" or isinstance(source, dict):
        if not isinstance(source, dict):
            return None, [
                ValidationMessage(
                    level="error",
                    source="io",
                    path="(root)",
                    message="Expected a dict for source_kind='data'.",
                )
            ]
        return source, errors

    if not isinstance(source, str):
        return None, [
            ValidationMessage(
                level="error",
                source="io",
                path="(root)",
                message=f"Unsupported source type: {type(source).__name__}",
            )
        ]

    if source_kind == "path" or (source_kind is None and (os.path.exists(source) or not _looks_like_yaml_text(source))):
        if not os.path.exists(source):
            return None, [ValidationMessage(level="error", source="io", path="(root)", message=f"File not found: {source}")]
        try:
            with open(source, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            return None, [ValidationMessage(level="error", source="io", path="(root)", message=f"Failed to read file {source}: {e}")]
    else:
        text = source

    try:
        import yaml
    except Exception:
        return None, [ValidationMessage(level="error", source="io", path="(root)", message="PyYAML is required to parse YAML: pip install pyyaml")]

    try:
        data = yaml.safe_load(text)
    except Exception as e:
        return None, [ValidationMessage(level="error", source="io", path="(root)", message=f"Failed to parse YAML: {e}")]

    if not isinstance(data, dict):
        return None, [
            ValidationMessage(
                level="error",
                source="io",
                path="(root)",
                message="CRML document must parse to a YAML mapping (object/dict) at the root.",
            )
        ]

    return data, errors


def _jsonschema_path(error) -> str:
    try:
        if error.path:
            return " -> ".join(map(str, error.path))
    except Exception:
        pass
    return "(root)"


def _format_jsonschema_error(error) -> str:
    if getattr(error, "validator", None) == "const":
        return f"Expected '{error.validator_value}', got '{error.instance}'"

    if getattr(error, "validator", None) == "oneOf":
        instance = getattr(error, "instance", None)
        if isinstance(instance, dict):
            if "mu" in instance and "median" in instance:
                return "Cannot use both 'median' and 'mu'. Choose one (median is recommended)."
            if "single_losses" in instance and any(k in instance for k in ("median", "mu", "sigma")):
                return "When using 'single_losses', do not also set 'median', 'mu', or 'sigma'."
            if "single_losses" in instance:
                return "'single_losses' must be an array with at least 2 positive values. It replaces median/mu/sigma by auto-calibration."
        return error.message

    if getattr(error, "validator", None) == "required":
        missing = None
        try:
            missing = error.validator_value[0]
        except Exception:
            pass
        if missing:
            return f"Missing required property: '{missing}'"
        return error.message

    if getattr(error, "validator", None) == "enum":
        try:
            values = ", ".join(map(str, error.validator_value))
            return f"Value must be one of: {values}"
        except Exception:
            return error.message

    return error.message


def _control_ids_from_controls(value: Any) -> list[str]:
    """Normalize control references to a list of control ids."""

    if not isinstance(value, list):
        return []

    ids: list[str] = []
    for item in value:
        if isinstance(item, str):
            ids.append(item)
            continue

        if isinstance(item, dict) and isinstance(item.get("id"), str):
            ids.append(item["id"])
            continue

        cid = getattr(item, "id", None)
        if isinstance(cid, str):
            ids.append(cid)

    return ids
