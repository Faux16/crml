from __future__ import annotations

from typing import Any, Literal

from jsonschema import Draft202012Validator
from pydantic import ValidationError

from .common import (
    ValidationMessage,
    ValidationReport,
    CONTROL_CATALOG_SCHEMA_PATH,
    _load_input,
    _load_control_catalog_schema,
    _jsonschema_path,
    _format_jsonschema_error,
)


ROOT_PATH = "(root)"


def _validate_control_catalog_schema(data: dict[str, Any]) -> list[ValidationMessage]:
    validator = Draft202012Validator(_load_control_catalog_schema())
    errors: list[ValidationMessage] = []
    for err in validator.iter_errors(data):
        errors.append(
            ValidationMessage(
                level="error",
                source="schema",
                path=_jsonschema_path(err),
                message=_format_jsonschema_error(err),
                validator=getattr(err, "validator", None),
            )
        )
    return errors


def _semantic_validate_control_catalog(data: dict[str, Any]) -> list[ValidationMessage]:
    catalog = data.get("catalog")
    controls = catalog.get("controls") if isinstance(catalog, dict) else None
    if not isinstance(controls, list):
        return []

    ids: list[str] = []
    errors: list[ValidationMessage] = []

    for idx, control in enumerate(controls):
        if not isinstance(control, dict):
            continue
        cid = control.get("id")
        if isinstance(cid, str):
            ids.append(cid)
            continue

        errors.append(
            ValidationMessage(
                level="error",
                source="semantic",
                path=f"catalog -> controls -> {idx} -> id",
                message="Control catalog entry 'id' must be a string.",
            )
        )

    if len(ids) != len(set(ids)):
        errors.append(
            ValidationMessage(
                level="error",
                source="semantic",
                path="catalog -> controls",
                message="Control catalog contains duplicate control ids.",
            )
        )

    return errors


def _strict_pydantic_validate(data: dict[str, Any]) -> list[ValidationMessage]:
    try:
        from ..models.control_catalog_model import CRControlCatalog

        CRControlCatalog.model_validate(data)
    except ValidationError as e:
        return [
            ValidationMessage(
                level="error",
                source="pydantic",
                path=ROOT_PATH,
                message=f"Pydantic validation failed: {e}",
                validator="pydantic",
            )
        ]
    return []


def validate_control_catalog(
    source: str | dict[str, Any],
    *,
    source_kind: Literal["path", "yaml", "data"] | None = None,
    strict_model: bool = False,
) -> ValidationReport:
    """Validate a CRML Control Catalog document."""

    data, io_errors = _load_input(source, source_kind=source_kind)
    if io_errors:
        return ValidationReport(ok=False, errors=io_errors, warnings=[])
    if data is None:
        return ValidationReport(
            ok=False,
            errors=[
                ValidationMessage(
                    level="error",
                    source="io",
                    path=ROOT_PATH,
                    message="No input data loaded.",
                )
            ],
            warnings=[],
        )

    try:
        errors = _validate_control_catalog_schema(data)
    except FileNotFoundError:
        return ValidationReport(
            ok=False,
            errors=[
                ValidationMessage(
                    level="error",
                    source="io",
                    path=ROOT_PATH,
                    message=f"Schema file not found at {CONTROL_CATALOG_SCHEMA_PATH}",
                )
            ],
            warnings=[],
        )
    warnings: list[ValidationMessage] = []

    if not errors:
        errors.extend(_semantic_validate_control_catalog(data))

    if strict_model and not errors:
        errors.extend(_strict_pydantic_validate(data))

    return ValidationReport(ok=not errors, errors=errors, warnings=warnings)
