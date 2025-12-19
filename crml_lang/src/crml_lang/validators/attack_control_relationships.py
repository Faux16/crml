from __future__ import annotations

from typing import Any, Literal

from jsonschema import Draft202012Validator

from .common import (
    ValidationMessage,
    ValidationReport,
    ATTACK_CONTROL_RELATIONSHIPS_SCHEMA_PATH,
    _load_input,
    _load_attack_control_relationships_schema,
    _jsonschema_path,
    _format_jsonschema_error,
)


def _schema_validation_errors(*, data: dict[str, Any]) -> list[ValidationMessage]:
    """Validate attack-control relationships data against the JSON schema and return errors."""
    validator = Draft202012Validator(_load_attack_control_relationships_schema())
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
    return ValidationMessage(level="error", source="semantic", path=path, message=message)


def _extract_relationship_groups(data: dict[str, Any]) -> list[Any] | None:
    payload = data.get("relationships")
    rels = payload.get("relationships") if isinstance(payload, dict) else None
    return rels if isinstance(rels, list) else None


def _validate_target_entry(
    *,
    rel_index: int,
    target_index: int,
    attack_id: str,
    target_entry: Any,
    errors: list[ValidationMessage],
    keys: list[tuple[str, str, str]],
) -> None:
    if not isinstance(target_entry, dict):
        errors.append(
            _semantic_error(
                path=f"relationships -> relationships -> {rel_index} -> targets -> {target_index}",
                message="Each target entry must be an object with at least 'control' and 'relationship_type'.",
            )
        )
        return

    control_id = target_entry.get("control")
    rtype = target_entry.get("relationship_type")
    rtype_norm = rtype if isinstance(rtype, str) else ""

    if not isinstance(control_id, str):
        errors.append(
            _semantic_error(
                path=f"relationships -> relationships -> {rel_index} -> targets -> {target_index} -> control",
                message="Target entry 'control' must be a string control id.",
            )
        )
        return

    keys.append((attack_id, control_id, rtype_norm))


def _validate_group_entry(
    *,
    rel_index: int,
    entry: Any,
    errors: list[ValidationMessage],
    attacks: list[str],
    keys: list[tuple[str, str, str]],
) -> None:
    if not isinstance(entry, dict):
        errors.append(
            _semantic_error(
                path=f"relationships -> relationships -> {rel_index}",
                message="Each relationship entry must be an object with 'attack' and 'targets'.",
            )
        )
        return

    attack_id = entry.get("attack")
    targets = entry.get("targets")

    if not isinstance(attack_id, str):
        errors.append(
            _semantic_error(
                path=f"relationships -> relationships -> {rel_index} -> attack",
                message="Relationship 'attack' must be a string attack-pattern id.",
            )
        )
        return

    attacks.append(attack_id)

    if not isinstance(targets, list) or not targets:
        errors.append(
            _semantic_error(
                path=f"relationships -> relationships -> {rel_index} -> targets",
                message="Relationship 'targets' must be a non-empty list.",
            )
        )
        return

    for j, t in enumerate(targets):
        _validate_target_entry(
            rel_index=rel_index,
            target_index=j,
            attack_id=attack_id,
            target_entry=t,
            errors=errors,
            keys=keys,
        )


def _semantic_validation_errors(*, data: dict[str, Any]) -> list[ValidationMessage]:
    errors: list[ValidationMessage] = []

    rels = _extract_relationship_groups(data)
    if rels is None:
        return errors

    attacks: list[str] = []
    keys: list[tuple[str, str, str]] = []

    for idx, r in enumerate(rels):
        _validate_group_entry(rel_index=idx, entry=r, errors=errors, attacks=attacks, keys=keys)

    # Encourage canonical 1:N representation: an attack should appear only once.
    if len(attacks) != len(set(attacks)):
        errors.append(
            ValidationMessage(
                level="error",
                source="semantic",
                path="relationships -> relationships",
                message="Attack-control relationships document contains duplicate attacks; group all targets under one attack.",
            )
        )

    # No duplicate (attack,control,relationship_type) mappings.
    if len(keys) != len(set(keys)):
        errors.append(
            ValidationMessage(
                level="error",
                source="semantic",
                path="relationships -> relationships",
                message="Attack-control relationships document contains duplicate (attack,control,relationship_type) mappings.",
            )
        )

    return errors


def validate_attack_control_relationships(
    source: str | dict[str, Any],
    *,
    source_kind: Literal["path", "yaml", "data"] | None = None,
    strict_model: bool = False,
) -> ValidationReport:
    """Validate a CRML Attack-to-Control Relationships document."""

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
                    message=f"Schema file not found at {ATTACK_CONTROL_RELATIONSHIPS_SCHEMA_PATH}",
                )
            ],
            warnings=[],
        )

    warnings: list[ValidationMessage] = []

    if not errors:
        errors.extend(_semantic_validation_errors(data=data))

    if strict_model and not errors:
        try:
            from ..models.attack_control_relationships_model import CRAttackControlRelationships

            CRAttackControlRelationships.model_validate(data)
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
