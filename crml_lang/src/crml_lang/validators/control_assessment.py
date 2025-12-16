from __future__ import annotations

from typing import Any, Literal, Optional

from jsonschema import Draft202012Validator

from .common import (
    ValidationMessage,
    ValidationReport,
    CONTROL_ASSESSMENT_SCHEMA_PATH,
    _load_input,
    _load_control_assessment_schema,
    _jsonschema_path,
    _format_jsonschema_error,
)
from .control_catalog import validate_control_catalog


def validate_control_assessment(
    source: str | dict[str, Any],
    *,
    source_kind: Literal["path", "yaml", "data"] | None = None,
    control_catalogs: Optional[list[str | dict[str, Any]]] = None,
    control_catalogs_source_kind: Literal["path", "yaml", "data"] | None = None,
    strict_model: bool = False,
) -> ValidationReport:
    """Validate a CRML Control Assessment Pack document."""

    data, io_errors = _load_input(source, source_kind=source_kind)
    if io_errors:
        return ValidationReport(ok=False, errors=io_errors, warnings=[])
    assert data is not None

    try:
        schema = _load_control_assessment_schema()
    except FileNotFoundError:
        return ValidationReport(
            ok=False,
            errors=[
                ValidationMessage(
                    level="error",
                    source="io",
                    path="(root)",
                    message=f"Schema file not found at {CONTROL_ASSESSMENT_SCHEMA_PATH}",
                )
            ],
            warnings=[],
        )

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

    if strict_model and not errors:
        try:
            from ..models.control_assessment_model import CRControlAssessmentSchema

            CRControlAssessmentSchema.model_validate(data)
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

    # Semantic checks
    if not errors:
        assessment = data.get("assessment")
        assessments = assessment.get("assessments") if isinstance(assessment, dict) else None
        if isinstance(assessments, list):
            ids: list[str] = []
            for idx, a in enumerate(assessments):
                if not isinstance(a, dict):
                    continue
                cid = a.get("id")
                if isinstance(cid, str):
                    ids.append(cid)
                else:
                    errors.append(
                        ValidationMessage(
                            level="error",
                            source="semantic",
                            path=f"assessment -> assessments -> {idx} -> id",
                            message="Control assessment entry 'id' must be a string.",
                        )
                    )

            if len(ids) != len(set(ids)):
                errors.append(
                    ValidationMessage(
                        level="error",
                        source="semantic",
                        path="assessment -> assessments",
                        message="Control assessment contains duplicate control ids.",
                    )
                )

            # Cross-pack check: if catalogs are provided, every assessment id must exist in them.
            if control_catalogs:
                catalog_ids: set[str] = set()
                for cidx, catalog_source in enumerate(control_catalogs):
                    catalog_data, catalog_io_errors = _load_input(
                        catalog_source,
                        source_kind=control_catalogs_source_kind,
                    )
                    if catalog_io_errors:
                        errors.extend(
                            [
                                ValidationMessage(
                                    level=e.level,
                                    source=e.source,
                                    path=f"control_catalogs -> {cidx} -> {e.path}",
                                    message=e.message,
                                    validator=e.validator,
                                )
                                for e in catalog_io_errors
                            ]
                        )
                        continue
                    assert catalog_data is not None

                    # Validate catalog itself first (schema + semantic).
                    cat_report = validate_control_catalog(catalog_data, source_kind="data")
                    if not cat_report.ok:
                        errors.extend(
                            [
                                ValidationMessage(
                                    level=e.level,
                                    source=e.source,
                                    path=f"control_catalogs -> {cidx} -> {e.path}",
                                    message=e.message,
                                    validator=e.validator,
                                )
                                for e in cat_report.errors
                            ]
                        )
                        continue

                    catalog = catalog_data.get("catalog")
                    controls = catalog.get("controls") if isinstance(catalog, dict) else None
                    if isinstance(controls, list):
                        for entry in controls:
                            if isinstance(entry, dict) and isinstance(entry.get("id"), str):
                                catalog_ids.add(entry["id"])

                if catalog_ids:
                    for cid in ids:
                        if cid not in catalog_ids:
                            errors.append(
                                ValidationMessage(
                                    level="error",
                                    source="semantic",
                                    path="assessment -> assessments -> id",
                                    message=f"Control assessment references unknown control id '{cid}' (not found in provided control catalog pack(s)).",
                                )
                            )

    return ValidationReport(ok=(len(errors) == 0), errors=errors, warnings=[])
