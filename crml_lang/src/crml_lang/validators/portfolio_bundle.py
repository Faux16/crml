from __future__ import annotations

from typing import Any, Literal

from jsonschema import Draft202012Validator

from .common import (
    PORTFOLIO_BUNDLE_SCHEMA_PATH,
    ValidationMessage,
    ValidationReport,
    _format_jsonschema_error,
    _jsonschema_path,
    _load_input,
    _load_portfolio_bundle_schema,
)


_ROOT_PATH = "(root)"
_CURRENT_VERSION = "1.0"


def _warn_non_current_version(*, data: dict[str, Any], warnings: list[ValidationMessage]) -> None:
    """Emit a warning if the portfolio bundle document version is not current."""
    if data.get("crml_portfolio_bundle") != _CURRENT_VERSION:
        warnings.append(
            ValidationMessage(
                level="warning",
                source="semantic",
                path="crml_portfolio_bundle",
                message=(
                    f"CRML portfolio bundle version '{data.get('crml_portfolio_bundle')}' is not current. "
                    f"Consider upgrading to '{_CURRENT_VERSION}'."
                ),
            )
        )


def _schema_errors(data: dict[str, Any]) -> list[ValidationMessage]:
    """Validate portfolio bundle data against the JSON schema and return errors."""
    schema = _load_portfolio_bundle_schema()
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


def _pydantic_strict_model_errors(data: dict[str, Any]) -> list[ValidationMessage]:
    """Run strict Pydantic model validation and return errors (best-effort)."""
    errors: list[ValidationMessage] = []
    try:
        from ..models.portfolio_bundle import CRPortfolioBundle

        CRPortfolioBundle.model_validate(data)
    except Exception as e:
        try:
            pydantic_errors = e.errors()  # type: ignore[attr-defined]
        except Exception:
            pydantic_errors = None

        if isinstance(pydantic_errors, list):
            for pe in pydantic_errors:
                loc = pe.get("loc", ())
                path = " -> ".join(map(str, loc)) if loc else _ROOT_PATH
                errors.append(
                    ValidationMessage(
                        level="error",
                        source="pydantic",
                        path=path,
                        message=str(pe.get("msg", "Pydantic validation failed")),
                        validator="pydantic",
                    )
                )
        else:
            errors.append(
                ValidationMessage(
                    level="error",
                    source="pydantic",
                    path=_ROOT_PATH,
                    message=f"Pydantic validation failed: {e}",
                    validator="pydantic",
                )
            )

    return errors


def _semantic_warnings(data: dict[str, Any]) -> list[ValidationMessage]:
    """Compute semantic (non-schema) warnings for a valid portfolio bundle document."""
    warnings: list[ValidationMessage] = []
    _warn_non_current_version(data=data, warnings=warnings)
    return warnings


def validate_portfolio_bundle(
    source: str | dict[str, Any],
    *,
    source_kind: Literal["path", "yaml", "data"] | None = None,
    strict_model: bool = False,
) -> ValidationReport:
    """Validate a CRML portfolio bundle document."""

    data, io_errors = _load_input(source, source_kind=source_kind)
    if io_errors:
        return ValidationReport(ok=False, errors=io_errors, warnings=[])
    assert data is not None

    try:
        errors = _schema_errors(data)
    except FileNotFoundError:
        return ValidationReport(
            ok=False,
            errors=[
                ValidationMessage(
                    level="error",
                    source="io",
                    path=_ROOT_PATH,
                    message=f"Schema file not found at {PORTFOLIO_BUNDLE_SCHEMA_PATH}",
                )
            ],
            warnings=[],
        )

    warnings = _semantic_warnings(data) if not errors else []

    if strict_model and not errors:
        errors.extend(_pydantic_strict_model_errors(data))

    return ValidationReport(ok=(len(errors) == 0), errors=errors, warnings=warnings)
