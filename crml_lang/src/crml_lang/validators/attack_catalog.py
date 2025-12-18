from __future__ import annotations

from typing import Any, Literal

from jsonschema import Draft202012Validator

from .common import (
    ValidationMessage,
    ValidationReport,
    ATTACK_CATALOG_SCHEMA_PATH,
    _load_input,
    _load_attack_catalog_schema,
    _jsonschema_path,
    _format_jsonschema_error,
)


def _load_schema_or_error() -> tuple[dict[str, Any] | None, list[ValidationMessage]]:
    """Load the attack catalog schema, returning a structured error on failure."""
    try:
        return _load_attack_catalog_schema(), []
    except FileNotFoundError:
        return (
            None,
            [
                ValidationMessage(
                    level="error",
                    source="io",
                    path="(root)",
                    message=f"Schema file not found at {ATTACK_CATALOG_SCHEMA_PATH}",
                )
            ],
        )


def _schema_validation_errors(schema: dict[str, Any], data: dict[str, Any]) -> list[ValidationMessage]:
    """Validate data against the provided JSON schema and return errors."""
    validator = Draft202012Validator(schema)
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


def _semantic_attack_id_errors(data: dict[str, Any]) -> list[ValidationMessage]:
    """Validate attack ids for presence/type and uniqueness."""
    catalog = data.get("catalog")
    attacks = catalog.get("attacks") if isinstance(catalog, dict) else None
    if not isinstance(attacks, list):
        return []

    errors: list[ValidationMessage] = []
    ids: list[str] = []
    for idx, attack in enumerate(attacks):
        if not isinstance(attack, dict):
            continue
        aid = attack.get("id")
        if isinstance(aid, str):
            ids.append(aid)
            continue
        errors.append(
            ValidationMessage(
                level="error",
                source="semantic",
                path=f"catalog -> attacks -> {idx} -> id",
                message="Attack catalog entry 'id' must be a string.",
            )
        )

    if len(ids) != len(set(ids)):
        errors.append(
            ValidationMessage(
                level="error",
                source="semantic",
                path="catalog -> attacks",
                message="Attack catalog contains duplicate attack ids.",
            )
        )

    return errors


def _pydantic_strict_errors(data: dict[str, Any]) -> list[ValidationMessage]:
    """Validate using the Pydantic model (strict mode)."""
    try:
        from ..models.attack_catalog_model import CRAttackCatalogSchema

        CRAttackCatalogSchema.model_validate(data)
        return []
    except Exception as e:
        return [
            ValidationMessage(
                level="error",
                source="pydantic",
                path="(root)",
                message=f"Pydantic validation failed: {e}",
                validator="pydantic",
            )
        ]


def validate_attack_catalog(
    source: str | dict[str, Any],
    *,
    source_kind: Literal["path", "yaml", "data"] | None = None,
    strict_model: bool = False,
) -> ValidationReport:
    """Validate a CRML Attack Cataloge document."""

    data, io_errors = _load_input(source, source_kind=source_kind)
    if io_errors:
        return ValidationReport(ok=False, errors=io_errors, warnings=[])
    assert data is not None

    schema, schema_errors = _load_schema_or_error()
    if schema_errors:
        return ValidationReport(ok=False, errors=schema_errors, warnings=[])
    assert schema is not None

    errors = _schema_validation_errors(schema, data)

    warnings: list[ValidationMessage] = []

    if not errors:
        errors.extend(_semantic_attack_id_errors(data))

    if strict_model and not errors:
        errors.extend(_pydantic_strict_errors(data))

    return ValidationReport(ok=(len(errors) == 0), errors=errors, warnings=warnings)
