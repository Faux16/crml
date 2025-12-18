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
    """Validate relationships data against the JSON schema and return errors."""
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


def _semantic_error(*, path: str, message: str) -> ValidationMessage:
    """Helper to build a semantic validation error at a given path."""
    return ValidationMessage(
        level="error",
        source="semantic",
        path=path,
        message=message,
    )


def _extract_relationship_groups(data: dict[str, Any]) -> list[Any] | None:
    """Extract the list of relationship entries from the document payload."""
    payload = data.get("relationships")
    rels = payload.get("relationships") if isinstance(payload, dict) else None
    return rels if isinstance(rels, list) else None


def _validate_relationship_target_entry(
    *,
    rel_index: int,
    target_index: int,
    source_id: str,
    target_entry: Any,
    errors: list[ValidationMessage],
    keys: list[tuple[str, str, str]],
) -> None:
    """Validate one relationship target entry and collect semantic errors."""
    if not isinstance(target_entry, dict):
        errors.append(
            _semantic_error(
                path=f"relationships -> relationships -> {rel_index} -> targets -> {target_index}",
                message="Each target entry must be an object with at least 'target' and 'overlap'.",
            )
        )
        return

    target_id = target_entry.get("target")
    rtype = target_entry.get("relationship_type")
    rtype_norm = rtype if isinstance(rtype, str) else ""

    if not isinstance(target_id, str):
        errors.append(
            _semantic_error(
                path=f"relationships -> relationships -> {rel_index} -> targets -> {target_index} -> target",
                message="Relationship target entry 'target' must be a string control id.",
            )
        )
        return

    keys.append((source_id, target_id, rtype_norm))

    if source_id == target_id:
        errors.append(
            _semantic_error(
                path=f"relationships -> relationships -> {rel_index} -> targets -> {target_index}",
                message="Relationship source and target must not be the same control id.",
            )
        )


def _validate_relationship_group_entry(
    *,
    rel_index: int,
    entry: Any,
    errors: list[ValidationMessage],
    sources: list[str],
    keys: list[tuple[str, str, str]],
) -> None:
    """Validate one relationship group entry (source + targets)."""
    if not isinstance(entry, dict):
        errors.append(
            _semantic_error(
                path=f"relationships -> relationships -> {rel_index}",
                message="Each relationship entry must be an object with 'source' and 'targets'.",
            )
        )
        return

    source_id = entry.get("source")
    targets = entry.get("targets")

    if not isinstance(source_id, str):
        errors.append(
            _semantic_error(
                path=f"relationships -> relationships -> {rel_index} -> source",
                message="Relationship 'source' must be a string control id.",
            )
        )
        return

    sources.append(source_id)

    if not isinstance(targets, list) or not targets:
        errors.append(
            _semantic_error(
                path=f"relationships -> relationships -> {rel_index} -> targets",
                message="Relationship 'targets' must be a non-empty list.",
            )
        )
        return

    for j, t in enumerate(targets):
        _validate_relationship_target_entry(
            rel_index=rel_index,
            target_index=j,
            source_id=source_id,
            target_entry=t,
            errors=errors,
            keys=keys,
        )


def _semantic_validation_errors(*, data: dict[str, Any]) -> list[ValidationMessage]:
    """Run semantic (cross-field) checks for control relationships documents."""
    errors: list[ValidationMessage] = []

    rels = _extract_relationship_groups(data)
    if rels is None:
        return errors

    sources: list[str] = []
    keys: list[tuple[str, str, str]] = []

    for idx, r in enumerate(rels):
        _validate_relationship_group_entry(
            rel_index=idx,
            entry=r,
            errors=errors,
            sources=sources,
            keys=keys,
        )

    # Encourage canonical 1:N representation: a source should appear only once.
    if len(sources) != len(set(sources)):
        errors.append(
            ValidationMessage(
                level="error",
                source="semantic",
                path="relationships -> relationships",
                message="Control relationships document contains duplicate sources; group all targets under one source.",
            )
        )

    # No duplicate (source,target,relationship_type) mappings.
    if len(keys) != len(set(keys)):
        errors.append(
            ValidationMessage(
                level="error",
                source="semantic",
                path="relationships -> relationships",
                message="Control relationships document contains duplicate (source,target,relationship_type) mappings.",
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
