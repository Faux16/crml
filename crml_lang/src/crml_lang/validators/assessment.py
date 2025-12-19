from __future__ import annotations

from typing import Any, Literal, Optional

from jsonschema import Draft202012Validator

from .common import (
    ValidationMessage,
    ValidationReport,
    ASSESSMENT_SCHEMA_PATH,
    ROOT_PATH,
    _load_input,
    _load_assessment_schema,
    _jsonschema_path,
    _format_jsonschema_error,
)
from .control_catalog import validate_control_catalog


def _wrap_messages(messages: list[ValidationMessage], *, prefix: str) -> list[ValidationMessage]:
    """Prefix message paths when nesting validation results."""
    out: list[ValidationMessage] = []
    for m in messages:
        out.append(
            ValidationMessage(
                level=m.level,
                source=m.source,
                path=f"{prefix} -> {m.path}" if m.path else prefix,
                message=m.message,
                validator=m.validator,
            )
        )
    return out


def _validate_against_schema(data: dict[str, Any]) -> list[ValidationMessage]:
    """Validate assessment data against the JSON schema."""
    try:
        schema = _load_assessment_schema()
    except FileNotFoundError:
        return [
            ValidationMessage(
                level="error",
                source="io",
                path=ROOT_PATH,
                message=f"Schema file not found at {ASSESSMENT_SCHEMA_PATH}",
            )
        ]

    validator = Draft202012Validator(schema)
    out: list[ValidationMessage] = []
    for err in validator.iter_errors(data):
        out.append(
            ValidationMessage(
                level="error",
                source="schema",
                path=_jsonschema_path(err),
                message=_format_jsonschema_error(err),
                validator=getattr(err, "validator", None),
            )
        )
    return out


def _strict_validate_model(data: dict[str, Any]) -> Optional[ValidationMessage]:
    """Validate against the Pydantic model and return a single error (if any)."""
    try:
        from ..models.assessment_model import CRAssessment

        CRAssessment.model_validate(data)
        return None
    except Exception as e:
        return ValidationMessage(
            level="error",
            source="pydantic",
            path=ROOT_PATH,
            message=f"Pydantic validation failed: {e}",
            validator="pydantic",
        )


def _collect_assessment_ids(data: dict[str, Any]) -> tuple[list[str], list[ValidationMessage]]:
    """Collect assessment ids and report per-entry type errors."""
    assessment = data.get("assessment")
    assessments = assessment.get("assessments") if isinstance(assessment, dict) else None
    if not isinstance(assessments, list):
        return [], []

    ids: list[str] = []
    errors: list[ValidationMessage] = []
    for idx, a in enumerate(assessments):
        if not isinstance(a, dict):
            continue
        cid = a.get("id")
        if isinstance(cid, str):
            ids.append(cid)
            continue
        errors.append(
            ValidationMessage(
                level="error",
                source="semantic",
                path=f"assessment -> assessments -> {idx} -> id",
                message="Assessment entry 'id' must be a string.",
            )
        )
    return ids, errors


def _check_duplicate_ids(ids: list[str]) -> Optional[ValidationMessage]:
    """Return an error if the id list contains duplicates."""
    if len(ids) == len(set(ids)):
        return None
    return ValidationMessage(
        level="error",
        source="semantic",
        path="assessment -> assessments",
        message="Assessment contains duplicate control ids.",
    )


def _collect_control_catalog_ids(
    control_catalogs: list[str | dict[str, Any]],
    *,
    source_kind: Literal["path", "yaml", "data"] | None,
) -> tuple[set[str], list[ValidationMessage]]:
    """Extract the set of control ids from provided control catalog documents."""
    catalog_ids: set[str] = set()
    errors: list[ValidationMessage] = []

    for cidx, catalog_source in enumerate(control_catalogs):
        catalog_data, catalog_io_errors = _load_input(catalog_source, source_kind=source_kind)
        if catalog_io_errors:
            errors.extend(_wrap_messages(catalog_io_errors, prefix=f"control_catalogs -> {cidx}"))
            continue
        assert catalog_data is not None

        cat_report = validate_control_catalog(catalog_data, source_kind="data")
        if not cat_report.ok:
            errors.extend(_wrap_messages(cat_report.errors, prefix=f"control_catalogs -> {cidx}"))
            continue

        catalog = catalog_data.get("catalog")
        controls = catalog.get("controls") if isinstance(catalog, dict) else None
        if not isinstance(controls, list):
            continue

        for entry in controls:
            if isinstance(entry, dict) and isinstance(entry.get("id"), str):
                catalog_ids.add(entry["id"])

    return catalog_ids, errors


def _check_ids_in_catalogs(ids: list[str], catalog_ids: set[str]) -> list[ValidationMessage]:
    """Validate that each assessment id exists in the referenced control catalog ids."""
    if not catalog_ids:
        return []
    out: list[ValidationMessage] = []
    for cid in ids:
        if cid in catalog_ids:
            continue
        out.append(
            ValidationMessage(
                level="error",
                source="semantic",
                path="assessment -> assessments -> id",
                message=(
                    f"Assessment references unknown control id '{cid}' (not found in provided control catalog(s))."
                ),
            )
        )
    return out


def validate_assessment(
    source: str | dict[str, Any],
    *,
    source_kind: Literal["path", "yaml", "data"] | None = None,
    control_catalogs: Optional[list[str | dict[str, Any]]] = None,
    control_catalogs_source_kind: Literal["path", "yaml", "data"] | None = None,
    strict_model: bool = False,
) -> ValidationReport:
    """Validate a CRML Assessment Catalog document."""

    data, io_errors = _load_input(source, source_kind=source_kind)
    if io_errors:
        return ValidationReport(ok=False, errors=io_errors, warnings=[])
    assert data is not None

    errors: list[ValidationMessage] = []

    errors.extend(_validate_against_schema(data))

    if strict_model and not errors:
        strict_error = _strict_validate_model(data)
        if strict_error is not None:
            errors.append(strict_error)

    if not errors:
        ids, id_errors = _collect_assessment_ids(data)
        errors.extend(id_errors)

        dup = _check_duplicate_ids(ids)
        if dup is not None:
            errors.append(dup)

        if control_catalogs:
            catalog_ids, cat_errors = _collect_control_catalog_ids(
                control_catalogs,
                source_kind=control_catalogs_source_kind,
            )
            errors.extend(cat_errors)
            if not errors:
                errors.extend(_check_ids_in_catalogs(ids, catalog_ids))

    return ValidationReport(ok=(len(errors) == 0), errors=errors, warnings=[])


