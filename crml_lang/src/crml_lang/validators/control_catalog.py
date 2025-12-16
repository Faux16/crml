from __future__ import annotations

from typing import Any, Literal

from jsonschema import Draft202012Validator

from .common import (
    ValidationMessage,
    ValidationReport,
    CONTROL_CATALOG_SCHEMA_PATH,
    _load_input,
    _load_control_catalog_schema,
    _jsonschema_path,
    _format_jsonschema_error,
)


def validate_control_catalog(
    source: str | dict[str, Any],
    *,
    source_kind: Literal["path", "yaml", "data"] | None = None,
    strict_model: bool = False,
) -> ValidationReport:
    """Validate a CRML Control Catalog Pack document."""

    data, io_errors = _load_input(source, source_kind=source_kind)
    if io_errors:
        return ValidationReport(ok=False, errors=io_errors, warnings=[])
    assert data is not None

    try:
        schema = _load_control_catalog_schema()
    except FileNotFoundError:
        return ValidationReport(
            ok=False,
            errors=[
                ValidationMessage(
                    level="error",
                    source="io",
                    path="(root)",
                    message=f"Schema file not found at {CONTROL_CATALOG_SCHEMA_PATH}",
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

    warnings: list[ValidationMessage] = []

    # Semantic checks
    if not errors:
        catalog = data.get("catalog")
        controls = catalog.get("controls") if isinstance(catalog, dict) else None
        if isinstance(controls, list):
            ids: list[str] = []
            for idx, c in enumerate(controls):
                if not isinstance(c, dict):
                    continue
                cid = c.get("id")
                if isinstance(cid, str):
                    ids.append(cid)
                else:
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

    if strict_model and not errors:
        try:
            from ..models.control_catalog_model import CRControlCatalogSchema

            CRControlCatalogSchema.model_validate(data)
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
