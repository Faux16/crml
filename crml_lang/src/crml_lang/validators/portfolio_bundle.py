from typing import Any, Literal, Union, Optional

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

    # Bundle completeness warnings for control context.
    # If any inlined scenario references controls, the bundle should carry enough
    # context for engines/tools to resolve and apply them. In CRML v1, that
    # context typically comes from:
    # - portfolio control inventory (portfolio_bundle.portfolio.portfolio.controls)
    # - inlined assessments packs (portfolio_bundle.assessments)
    # - inlined control-relationships packs (portfolio_bundle.control_relationships)
    # We warn if *either* the inventory/assessment context is missing OR the
    # control-relationships packs are missing.
    try:
        pb = data.get("portfolio_bundle")
        if isinstance(pb, dict):
            scenarios = pb.get("scenarios")
            has_scenario_controls = False
            if isinstance(scenarios, list):
                for entry in scenarios:
                    if not isinstance(entry, dict):
                        continue
                    sc_doc = entry.get("scenario")
                    if not isinstance(sc_doc, dict):
                        continue
                    sc_payload = sc_doc.get("scenario")
                    if not isinstance(sc_payload, dict):
                        continue
                    controls = sc_payload.get("controls")
                    if isinstance(controls, list) and len(controls) > 0:
                        has_scenario_controls = True
                        break

            if has_scenario_controls:
                portfolio_doc = pb.get("portfolio")
                portfolio_payload = None
                if isinstance(portfolio_doc, dict):
                    portfolio_payload = portfolio_doc.get("portfolio")

                inventory_controls = None
                if isinstance(portfolio_payload, dict):
                    inventory_controls = portfolio_payload.get("controls")

                has_inventory = isinstance(inventory_controls, list) and len(inventory_controls) > 0
                has_assessments = isinstance(pb.get("assessments"), list) and len(pb.get("assessments") or []) > 0
                has_control_context = has_inventory or has_assessments

                has_relationships = isinstance(pb.get("control_relationships"), list) and len(pb.get("control_relationships") or []) > 0

                missing_bits: list[str] = []
                if not has_control_context:
                    missing_bits.append(
                        "control context (portfolio controls inventory and/or inlined assessments packs)"
                    )
                if not has_relationships:
                    missing_bits.append("control relationship packs (control-to-control mappings)")

                if missing_bits:
                    warnings.append(
                        ValidationMessage(
                            level="warning",
                            source="semantic",
                            path="portfolio_bundle",
                            message=(
                                "One or more inlined scenarios reference controls, but the bundle is missing "
                                + " and ".join(missing_bits)
                                + ". Engines may be unable to resolve/apply controls. "
                                "Consider bundling the needed artifacts (e.g. include portfolio controls, assessments, and control_relationships)."
                            ),
                        )
                    )
    except Exception:
        # Best-effort warning only; never fail validation for this check.
        pass

    return warnings


def validate_portfolio_bundle(
    source: Union[str, dict[str, Any]],
    *,
    source_kind: Optional[Literal["path", "yaml", "data"]] = None,
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
