from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any, Literal, Optional

from ..yamlio import load_yaml_mapping_from_str


# Package root: .../crml_lang
_PACKAGE_DIR = Path(__file__).resolve().parents[1]
_SCHEMA_DIR = _PACKAGE_DIR / "schemas"

ROOT_PATH = "(root)"

SCENARIO_SCHEMA_PATH = str(_SCHEMA_DIR / "crml-scenario-schema.json")
PORTFOLIO_SCHEMA_PATH = str(_SCHEMA_DIR / "crml-portfolio-schema.json")
PORTFOLIO_BUNDLE_SCHEMA_PATH = str(_SCHEMA_DIR / "crml-portfolio-bundle-schema.json")
ASSESSMENT_SCHEMA_PATH = str(_SCHEMA_DIR / "crml-assessment-schema.json")
CONTROL_CATALOG_SCHEMA_PATH = str(_SCHEMA_DIR / "crml-control-catalog-schema.json")
ATTACK_CATALOG_SCHEMA_PATH = str(_SCHEMA_DIR / "crml-attack-catalog-schema.json")
ATTACK_CONTROL_RELATIONSHIPS_SCHEMA_PATH = str(
    _SCHEMA_DIR / "crml-attack-control-relationships-schema.json"
)
CONTROL_RELATIONSHIPS_SCHEMA_PATH = str(_SCHEMA_DIR / "crml-control-relationships-schema.json")


@dataclass(frozen=True)
class ValidationMessage:
    """A single validation message (error or warning)."""

    level: Literal["error", "warning"]
    message: str
    path: str = ROOT_PATH
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
    """Load a JSON schema file from disk."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_scenario_schema() -> dict[str, Any]:
    """Load the CRML Scenario JSON schema as a dict."""
    return _load_schema(SCENARIO_SCHEMA_PATH)


def _load_portfolio_schema() -> dict[str, Any]:
    """Load the CRML Portfolio JSON schema as a dict."""
    return _load_schema(PORTFOLIO_SCHEMA_PATH)


def _load_portfolio_bundle_schema() -> dict[str, Any]:
    """Load the CRML Portfolio Bundle JSON schema as a dict."""
    return _load_schema(PORTFOLIO_BUNDLE_SCHEMA_PATH)


def _load_assessment_schema() -> dict[str, Any]:
    """Load the CRML Assessment JSON schema as a dict.
    """
    return _load_schema(ASSESSMENT_SCHEMA_PATH)


def _load_control_catalog_schema() -> dict[str, Any]:
    """Load the CRML Control Catalog JSON schema as a dict."""
    return _load_schema(CONTROL_CATALOG_SCHEMA_PATH)


def _load_attack_catalog_schema() -> dict[str, Any]:
    """Load the CRML Attack Catalog JSON schema as a dict."""
    return _load_schema(ATTACK_CATALOG_SCHEMA_PATH)


def _load_attack_control_relationships_schema() -> dict[str, Any]:
    """Load the CRML Attack-to-Control Relationships JSON schema as a dict."""
    return _load_schema(ATTACK_CONTROL_RELATIONSHIPS_SCHEMA_PATH)


def _load_control_relationships_schema() -> dict[str, Any]:
    """Load the CRML Control Relationships JSON schema as a dict."""
    return _load_schema(CONTROL_RELATIONSHIPS_SCHEMA_PATH)


def _looks_like_yaml_text(s: str) -> bool:
    """Heuristically decide whether `s` is YAML text rather than a filesystem path."""
    # Heuristic: YAML documents almost always contain either newlines or key separators.
    return "\n" in s or ":" in s


def _error(message: str, *, path: str = ROOT_PATH) -> list[ValidationMessage]:
    """Create a single IO-scoped validation error."""
    return [ValidationMessage(level="error", source="io", path=path, message=message)]


def _read_text_file(path: str) -> tuple[Optional[str], list[ValidationMessage]]:
    """Read a UTF-8 text file and return (text, errors)."""
    if not os.path.exists(path):
        return None, _error(f"File not found: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read(), []
    except Exception as e:
        return None, _error(f"Failed to read file {path}: {e}")


def _parse_yaml_mapping(text: str) -> tuple[Optional[dict[str, Any]], list[ValidationMessage]]:
    """Parse YAML and require the root to be a mapping.

    Returns:
        A pair of (data, errors). On failure, data is None and errors is non-empty.
    """
    try:
        data = load_yaml_mapping_from_str(text)
    except ValueError:
        return None, _error("CRML document must parse to a YAML mapping (object/dict) at the root.")
    except Exception as e:
        return None, _error(f"Failed to parse YAML: {e}")

    return data, []


def _load_input(
    source: str | dict[str, Any],
    *,
    source_kind: Literal["path", "yaml", "data"] | None,
) -> tuple[Optional[dict[str, Any]], list[ValidationMessage]]:
    """Load CRML input from a path, YAML string, or already-parsed dict.

    This helper centralizes "input kind" inference and produces consistent
    IO errors for the validator modules.
    """
    if source_kind == "data" or isinstance(source, dict):
        if not isinstance(source, dict):
            return None, _error("Expected a dict for source_kind='data'.")
        return source, []

    if not isinstance(source, str):
        return None, _error(f"Unsupported source type: {type(source).__name__}")

    should_read_path = source_kind == "path" or (
        source_kind is None and (os.path.exists(source) or not _looks_like_yaml_text(source))
    )

    if should_read_path:
        text, read_errors = _read_text_file(source)
        if read_errors:
            return None, read_errors
        assert text is not None
        return _parse_yaml_mapping(text)

    return _parse_yaml_mapping(source)


def _jsonschema_path(error) -> str:
    """Convert a jsonschema error object's path into a readable string."""
    try:
        if error.path:
            return " -> ".join(map(str, error.path))
    except Exception:
        pass
    return ROOT_PATH


def _format_oneof_error(error) -> str:
    """Provide friendlier messages for common `oneOf` schema failures."""
    instance = getattr(error, "instance", None)
    if not isinstance(instance, dict):
        return error.message

    has_median = "median" in instance
    has_mu = "mu" in instance
    has_sigma = "sigma" in instance
    has_single_losses = "single_losses" in instance

    if has_mu and has_median:
        return "Cannot use both 'median' and 'mu'. Choose one (median is recommended)."

    if has_single_losses and (has_median or has_mu or has_sigma):
        return "When using 'single_losses', do not also set 'median', 'mu', or 'sigma'."

    if has_single_losses:
        return "'single_losses' must be an array with at least 2 positive values. It replaces median/mu/sigma by auto-calibration."

    return error.message


def _format_required_error(error) -> str:
    """Format jsonschema `required` errors to highlight the missing key."""
    try:
        missing = error.validator_value[0]
    except Exception:
        missing = None
    if missing:
        return f"Missing required property: '{missing}'"
    return error.message


def _format_enum_error(error) -> str:
    """Format jsonschema `enum` errors with the list of allowed values."""
    try:
        values = ", ".join(map(str, error.validator_value))
    except Exception:
        return error.message
    return f"Value must be one of: {values}"


def _format_jsonschema_error(error) -> str:
    """Format jsonschema errors with a few CRML-specific improvements."""
    validator = getattr(error, "validator", None)
    if validator == "const":
        return f"Expected '{error.validator_value}', got '{error.instance}'"
    if validator == "oneOf":
        return _format_oneof_error(error)
    if validator == "required":
        return _format_required_error(error)
    if validator == "enum":
        return _format_enum_error(error)
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
