from __future__ import annotations

from typing import Any, Literal, Tuple, Optional, Union

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


def _load_schema_or_error() -> Tuple[Optional[dict[str, Any]], list[ValidationMessage]]:
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


def _attack_catalog_get_attacks(doc: dict[str, Any]) -> list[Any] | None:
    catalog = doc.get("catalog")
    if not isinstance(catalog, dict):
        return None
    attacks = catalog.get("attacks")
    if not isinstance(attacks, list):
        return None
    return attacks


def _attack_catalog_get_prefix(doc: dict[str, Any]) -> str | None:
    catalog = doc.get("catalog")
    if not isinstance(catalog, dict):
        return None
    catalog_id = catalog.get("id")
    if not isinstance(catalog_id, str) or not catalog_id:
        return None
    return f"{catalog_id}:"


def _attack_catalog_collect_ids(attacks: list[Any], prefix: str | None) -> tuple[list[str], list[ValidationMessage]]:
    ids: list[str] = []
    errs: list[ValidationMessage] = []
    for idx, attack in enumerate(attacks):
        if not isinstance(attack, dict):
            continue
        aid = attack.get("id")
        if not isinstance(aid, str):
            errs.append(
                ValidationMessage(
                    level="error",
                    source="semantic",
                    path=f"catalog -> attacks -> {idx} -> id",
                    message="Attack catalog entry 'id' must be a string.",
                )
            )
            continue
        ids.append(aid)
        if prefix and not aid.startswith(prefix):
            errs.append(
                ValidationMessage(
                    level="error",
                    source="semantic",
                    path=f"catalog -> attacks -> {idx} -> id",
                    message=f"Attack id '{aid}' must begin with catalog namespace prefix '{prefix}'.",
                )
            )
    return ids, errs


def _attack_catalog_duplicate_id_errors(ids: list[str]) -> list[ValidationMessage]:
    if len(ids) == len(set(ids)):
        return []
    return [
        ValidationMessage(
            level="error",
            source="semantic",
            path="catalog -> attacks",
            message="Attack catalog contains duplicate attack ids.",
        )
    ]


def _attack_catalog_validate_parent_refs(
    attacks: list[Any],
    *,
    id_set: set[str],
    prefix: str | None,
) -> list[ValidationMessage]:
    errs: list[ValidationMessage] = []
    for idx, attack in enumerate(attacks):
        if not isinstance(attack, dict):
            continue
        aid = attack.get("id")
        if not isinstance(aid, str) or not aid:
            continue
        parent = attack.get("parent")
        if parent is None:
            continue
        if not isinstance(parent, str):
            errs.append(
                ValidationMessage(
                    level="error",
                    source="semantic",
                    path=f"catalog -> attacks -> {idx} -> parent",
                    message="Attack catalog entry 'parent' must be a string.",
                )
            )
            continue
        if prefix and not parent.startswith(prefix):
            errs.append(
                ValidationMessage(
                    level="error",
                    source="semantic",
                    path=f"catalog -> attacks -> {idx} -> parent",
                    message=f"Parent id '{parent}' must begin with catalog namespace prefix '{prefix}'.",
                )
            )
        if parent not in id_set:
            errs.append(
                ValidationMessage(
                    level="error",
                    source="semantic",
                    path=f"catalog -> attacks -> {idx} -> parent",
                    message=f"Parent id '{parent}' does not exist in this catalog.",
                )
            )
    return errs


def _attack_catalog_validate_phase_refs_for_attack(
    idx: int,
    *,
    attack: dict[str, Any],
    id_set: set[str],
    prefix: str | None,
) -> list[ValidationMessage]:
    phases = attack.get("phases")
    if phases is None:
        return []

    if not isinstance(phases, list) or any(not isinstance(p, str) for p in phases):
        return [
            ValidationMessage(
                level="error",
                source="semantic",
                path=f"catalog -> attacks -> {idx} -> phases",
                message="Attack catalog entry 'phases' must be a list of strings.",
            )
        ]

    errs: list[ValidationMessage] = []
    for phase_id in phases:
        if prefix and not phase_id.startswith(prefix):
            errs.append(
                ValidationMessage(
                    level="error",
                    source="semantic",
                    path=f"catalog -> attacks -> {idx} -> phases",
                    message=f"Phase id '{phase_id}' must begin with catalog namespace prefix '{prefix}'.",
                )
            )
        if phase_id not in id_set:
            errs.append(
                ValidationMessage(
                    level="error",
                    source="semantic",
                    path=f"catalog -> attacks -> {idx} -> phases",
                    message=f"Phase id '{phase_id}' does not exist in this catalog.",
                )
            )
    return errs


def _attack_catalog_validate_phase_refs(
    attacks: list[Any],
    *,
    id_set: set[str],
    prefix: str | None,
) -> list[ValidationMessage]:
    errs: list[ValidationMessage] = []
    for idx, attack in enumerate(attacks):
        if not isinstance(attack, dict):
            continue
        aid = attack.get("id")
        if not isinstance(aid, str) or not aid:
            continue
        errs.extend(
            _attack_catalog_validate_phase_refs_for_attack(
                idx,
                attack=attack,
                id_set=id_set,
                prefix=prefix,
            )
        )
    return errs


def _semantic_attack_id_errors(data: dict[str, Any]) -> list[ValidationMessage]:
    """Validate attack ids for presence/type, uniqueness, namespace alignment, and internal references."""

    attacks = _attack_catalog_get_attacks(data)
    if attacks is None:
        return []

    prefix = _attack_catalog_get_prefix(data)
    ids, errors = _attack_catalog_collect_ids(attacks, prefix)
    errors.extend(_attack_catalog_duplicate_id_errors(ids))

    id_set = set(ids)
    errors.extend(_attack_catalog_validate_parent_refs(attacks, id_set=id_set, prefix=prefix))
    errors.extend(_attack_catalog_validate_phase_refs(attacks, id_set=id_set, prefix=prefix))
    return errors


def _pydantic_strict_errors(data: dict[str, Any]) -> list[ValidationMessage]:
    """Validate using the Pydantic model (strict mode)."""
    try:
        from ..models.attack_catalog_model import CRAttackCatalog

        CRAttackCatalog.model_validate(data)
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
    source: Union[str, dict[str, Any]],
    *,
    source_kind: Optional[Literal["path", "yaml", "data"]] = None,
    strict_model: bool = False,
) -> ValidationReport:
    """Validate a CRML Attack Catalog document."""

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
