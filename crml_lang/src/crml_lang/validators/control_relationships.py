from __future__ import annotations

from typing import Any, Literal

from jsonschema import Draft202012Validator

from .common import (
    ValidationMessage,
    ValidationReport,
    CONTROL_RELATIONSHIPS_SCHEMA_PATH,
    _load_input,
    _load_control_relationships_schema,
    _jsonschema_path,
    _format_jsonschema_error,
)


def _schema_validation_errors(*, data: dict[str, Any]) -> list[ValidationMessage]:
    validator = Draft202012Validator(_load_control_relationships_schema())
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


def _semantic_validation_errors(*, data: dict[str, Any]) -> list[ValidationMessage]:
    errors: list[ValidationMessage] = []

    payload = data.get("relationships")
    rels = payload.get("relationships") if isinstance(payload, dict) else None
    if not isinstance(rels, list):
        return errors

    keys: list[tuple[str, str, str]] = []
    for idx, r in enumerate(rels):
        if not isinstance(r, dict):
            continue

        source_id = r.get("source")
        target_id = r.get("target")
        rtype = r.get("relationship_type")
        rtype_norm = rtype if isinstance(rtype, str) else ""

        if not isinstance(source_id, str):
            errors.append(
                ValidationMessage(
                    level="error",
                    source="semantic",
                    path=f"relationships -> relationships -> {idx} -> source",
                    message="Relationship 'source' must be a string control id.",
                )
            )
        if not isinstance(target_id, str):
            errors.append(
                ValidationMessage(
                    level="error",
                    source="semantic",
                    path=f"relationships -> relationships -> {idx} -> target",
                    message="Relationship 'target' must be a string control id.",
                )
            )

        if isinstance(source_id, str) and isinstance(target_id, str):
            keys.append((source_id, target_id, rtype_norm))
            if source_id == target_id:
                errors.append(
                    ValidationMessage(
                        level="error",
                        source="semantic",
                        path=f"relationships -> relationships -> {idx}",
                        message="Relationship source and target must not be the same control id.",
                    )
                )

    if len(keys) != len(set(keys)):
        errors.append(
            ValidationMessage(
                level="error",
                source="semantic",
                path="relationships -> relationships",
                message="Control relationships document contains duplicate relationship edges.",
            )
        )

    return errors


def validate_control_relationships(
    source: str | dict[str, Any],
    *,
    source_kind: Literal["path", "yaml", "data"] | None = None,
    strict_model: bool = False,
) -> ValidationReport:
    """Validate a CRML Control Relationships document."""

    data, io_errors = _load_input(source, source_kind=source_kind)
    if io_errors:
        return ValidationReport(ok=False, errors=io_errors, warnings=[])
    assert data is not None

    try:
        errors = _schema_validation_errors(data=data)
    except FileNotFoundError:
        return ValidationReport(
            ok=False,
            errors=[
                ValidationMessage(
                    level="error",
                    source="io",
                    path="(root)",
                    message=f"Schema file not found at {CONTROL_RELATIONSHIPS_SCHEMA_PATH}",
                )
            ],
            warnings=[],
        )

    warnings: list[ValidationMessage] = []

    # Semantic checks
    if not errors:
        errors.extend(_semantic_validation_errors(data=data))

    if strict_model and not errors:
        try:
            from ..models.control_relationships_model import CRControlRelationshipsSchema

            CRControlRelationshipsSchema.model_validate(data)
        except Exception as e:
            errors.append(
                ValidationMessage(
                    level="error",
                    source="pydantic",
                    path="(root)",
                    message=f"Pydantic validation failed: {e}",
                    validator="pydantic",
                )
            )

    return ValidationReport(ok=(len(errors) == 0), errors=errors, warnings=warnings)
