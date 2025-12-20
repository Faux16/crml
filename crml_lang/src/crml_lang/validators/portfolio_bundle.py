from typing import Any, Iterator, Literal, Optional, Union

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


def _is_nonempty_list(value: Any) -> bool:
    return isinstance(value, list) and len(value) > 0


def _iter_inlined_scenario_payloads(pb: dict[str, Any]) -> Iterator[dict[str, Any]]:
    scenarios = pb.get("scenarios")
    if not isinstance(scenarios, list):
        return

    for entry in scenarios:
        if not isinstance(entry, dict):
            continue
        sc_doc = entry.get("scenario")
        if not isinstance(sc_doc, dict):
            continue
        sc_payload = sc_doc.get("scenario")
        if not isinstance(sc_payload, dict):
            continue
        yield sc_payload


def _bundle_has_scenario_controls(pb: dict[str, Any]) -> bool:
    for sc_payload in _iter_inlined_scenario_payloads(pb):
        if _is_nonempty_list(sc_payload.get("controls")):
            return True
    return False


def _bundle_has_inventory_controls(pb: dict[str, Any]) -> bool:
    portfolio_doc = pb.get("portfolio")
    if not isinstance(portfolio_doc, dict):
        return False
    portfolio_payload = portfolio_doc.get("portfolio")
    if not isinstance(portfolio_payload, dict):
        return False
    return _is_nonempty_list(portfolio_payload.get("controls"))


def _bundle_has_assessments(pb: dict[str, Any]) -> bool:
    return _is_nonempty_list(pb.get("assessments"))


def _bundle_has_control_relationships(pb: dict[str, Any]) -> bool:
    return _is_nonempty_list(pb.get("control_relationships"))


def _warn_missing_control_artifacts_for_inlined_scenarios(
    pb: dict[str, Any], warnings: list[ValidationMessage]
) -> None:
    if not _bundle_has_scenario_controls(pb):
        return

    has_control_context = _bundle_has_inventory_controls(pb) or _bundle_has_assessments(pb)
    has_relationships = _bundle_has_control_relationships(pb)

    missing_bits: list[str] = []
    if not has_control_context:
        missing_bits.append("control context (portfolio controls inventory and/or inlined assessments packs)")
    if not has_relationships:
        missing_bits.append("control relationship packs (control-to-control mappings)")

    if not missing_bits:
        return

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
            _warn_missing_control_artifacts_for_inlined_scenarios(pb, warnings)
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
