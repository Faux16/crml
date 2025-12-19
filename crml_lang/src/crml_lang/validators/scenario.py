from __future__ import annotations

from typing import Any, Literal

from jsonschema import Draft202012Validator

from .common import (
    ValidationMessage,
    ValidationReport,
    SCENARIO_SCHEMA_PATH,
    _load_input,
    _load_scenario_schema,
    _jsonschema_path,
    _format_jsonschema_error,
    _control_ids_from_controls,
)


_ROOT_PATH = "(root)"
_CURRENT_VERSION = "1.0"
_RECOMMENDED_META_KEYS = ("version", "description", "author", "industries")


def _warn_non_current_version(*, data: dict[str, Any], warnings: list[ValidationMessage]) -> None:
    """Emit a warning if the scenario document version is not the current one."""
    # Warn if using non-current CRML version
    # Note: the JSON schema currently enforces the version, so this is mainly
    # forward-compatible documentation for future schema relaxations.
    if data.get("crml_scenario") != _CURRENT_VERSION:
        warnings.append(
            ValidationMessage(
                level="warning",
                source="semantic",
                path="crml_scenario",
                message=(
                    f"CRML scenario version '{data.get('crml_scenario')}' is not current. "
                    f"Consider upgrading to '{_CURRENT_VERSION}'."
                ),
            )
        )


def _warn_missing_meta_fields(*, meta: dict[str, Any], warnings: list[ValidationMessage]) -> None:
    """Emit warnings for missing recommended `meta` keys."""
    for key in _RECOMMENDED_META_KEYS:
        if key not in meta or meta.get(key) in ([], ""):
            warnings.append(
                ValidationMessage(
                    level="warning",
                    source="semantic",
                    path=f"meta -> {key}",
                    message=(
                        f"'meta.{key}' is missing or empty. It is not required, "
                        "but strongly recommended for documentation and context."
                    ),
                )
            )


def _warn_missing_regions(*, locale: dict[str, Any], warnings: list[ValidationMessage]) -> None:
    """Emit a warning if `meta.locale.regions` is missing/empty."""
    if "regions" not in locale or locale.get("regions") in ([], ""):
        warnings.append(
            ValidationMessage(
                level="warning",
                source="semantic",
                path="meta -> locale -> regions",
                message=(
                    "'meta.locale.regions' is missing or empty. It is not required, "
                    "but strongly recommended for documentation and context."
                ),
            )
        )


def _warn_mixture_weights(*, severity: dict[str, Any], warnings: list[ValidationMessage]) -> None:
    """Emit a warning if mixture component weights do not sum to ~1."""
    # Warn if mixture weights don't sum to 1
    if severity.get("model") != "mixture" or not isinstance(severity.get("components"), list):
        return

    total_weight = 0.0
    for comp in severity.get("components", []):
        if not isinstance(comp, dict) or not comp:
            continue
        dist_key = next(iter(comp.keys()), None)
        if not dist_key:
            continue
        dist = comp.get(dist_key)
        if isinstance(dist, dict):
            total_weight += float(dist.get("weight", 0) or 0)

    if abs(total_weight - 1.0) > 0.001:
        warnings.append(
            ValidationMessage(
                level="warning",
                source="semantic",
                path="scenario -> severity -> components",
                message=f"Mixture weights sum to {total_weight:.3f}, should sum to 1.0",
            )
        )


def _warn_missing_currency(*, severity: dict[str, Any], warnings: list[ValidationMessage]) -> None:
    """Emit a warning if severity parameters appear monetary but omit `currency`."""
    # Warn if severity node appears to contain monetary values but no currency property
    params = severity.get("parameters", {}) if isinstance(severity.get("parameters"), dict) else {}
    has_money_fields = any(k in params for k in ("median", "mu", "mean", "single_losses"))
    if has_money_fields and "currency" not in params:
        warnings.append(
            ValidationMessage(
                level="warning",
                source="semantic",
                path="scenario -> severity -> parameters",
                message=(
                    "Severity node has monetary values but no 'currency' property. "
                    "Specify the currency to avoid implicit assumptions."
                ),
            )
        )


def _warn_duplicate_scenario_control_ids(*, scenario: dict[str, Any], warnings: list[ValidationMessage]) -> None:
    """Emit a warning if scenario control ids contain duplicates."""
    # Warn if scenario control ids contain duplicates
    scenario_controls = scenario.get("controls") if isinstance(scenario, dict) else None
    ids = _control_ids_from_controls(scenario_controls)
    if ids and len(ids) != len(set(ids)):
        warnings.append(
            ValidationMessage(
                level="warning",
                source="semantic",
                path="scenario -> controls",
                message="Scenario 'controls' contains duplicate control ids.",
            )
        )


def _schema_errors(data: dict[str, Any]) -> list[ValidationMessage]:
    """Validate scenario data against the JSON schema and return errors."""
    schema = _load_scenario_schema()
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
        from ..models.scenario_model import CRScenario

        CRScenario.model_validate(data)
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
    """Compute semantic (non-schema) warnings for a valid scenario document."""
    warnings: list[ValidationMessage] = []

    _warn_non_current_version(data=data, warnings=warnings)

    meta = data.get("meta", {}) if isinstance(data.get("meta"), dict) else {}
    _warn_missing_meta_fields(meta=meta, warnings=warnings)

    locale = meta.get("locale", {}) if isinstance(meta.get("locale"), dict) else {}
    _warn_missing_regions(locale=locale, warnings=warnings)

    scenario = data.get("scenario", {}) if isinstance(data.get("scenario"), dict) else {}
    severity = scenario.get("severity", {}) if isinstance(scenario.get("severity"), dict) else {}
    _warn_mixture_weights(severity=severity, warnings=warnings)
    _warn_missing_currency(severity=severity, warnings=warnings)
    _warn_duplicate_scenario_control_ids(scenario=scenario, warnings=warnings)

    return warnings


def validate(
    source: str | dict[str, Any],
    *,
    source_kind: Literal["path", "yaml", "data"] | None = None,
    strict_model: bool = False,
) -> ValidationReport:
    """Validate a CRML scenario document."""

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
                    message=f"Schema file not found at {SCENARIO_SCHEMA_PATH}",
                )
            ],
            warnings=[],
        )

    warnings = _semantic_warnings(data) if not errors else []

    if strict_model and not errors:
        errors.extend(_pydantic_strict_model_errors(data))

    return ValidationReport(ok=(len(errors) == 0), errors=errors, warnings=warnings)
