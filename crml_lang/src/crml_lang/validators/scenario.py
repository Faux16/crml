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


def _semantic_warnings(data: dict[str, Any]) -> list[ValidationMessage]:
    warnings: list[ValidationMessage] = []

    # Warn if using non-current CRML version
    # Note: the JSON schema currently enforces the version, so this is mainly
    # forward-compatible documentation for future schema relaxations.
    current_version = "1.0"
    if data.get("crml_scenario") != current_version:
        warnings.append(
            ValidationMessage(
                level="warning",
                source="semantic",
                path="crml_scenario",
                message=f"CRML scenario version '{data.get('crml_scenario')}' is not current. Consider upgrading to '{current_version}'.",
            )
        )

    meta = data.get("meta", {}) if isinstance(data.get("meta"), dict) else {}
    for key in ["version", "description", "author", "industries"]:
        if key not in meta or meta.get(key) in ([], ""):
            warnings.append(
                ValidationMessage(
                    level="warning",
                    source="semantic",
                    path=f"meta -> {key}",
                    message=f"'meta.{key}' is missing or empty. It is not required, but strongly recommended for documentation and context.",
                )
            )

    locale = meta.get("locale", {}) if isinstance(meta.get("locale"), dict) else {}
    if "regions" not in locale or locale.get("regions") in ([], ""):
        warnings.append(
            ValidationMessage(
                level="warning",
                source="semantic",
                path="meta -> locale -> regions",
                message="'meta.locale.regions' is missing or empty. It is not required, but strongly recommended for documentation and context.",
            )
        )

    scenario = data.get("scenario", {}) if isinstance(data.get("scenario"), dict) else {}
    severity = scenario.get("severity", {}) if isinstance(scenario.get("severity"), dict) else {}

    # Warn if mixture weights don't sum to 1
    if severity.get("model") == "mixture" and isinstance(severity.get("components"), list):
        total_weight = 0.0
        for comp in severity.get("components", []):
            if not isinstance(comp, dict) or not comp:
                continue
            dist_key = list(comp.keys())[0]
            if isinstance(comp.get(dist_key), dict):
                total_weight += float(comp[dist_key].get("weight", 0) or 0)
        if abs(total_weight - 1.0) > 0.001:
            warnings.append(
                ValidationMessage(
                    level="warning",
                    source="semantic",
                    path="scenario -> severity -> components",
                    message=f"Mixture weights sum to {total_weight:.3f}, should sum to 1.0",
                )
            )

    # Warn if severity node appears to contain monetary values but no currency property
    params = severity.get("parameters", {}) if isinstance(severity.get("parameters"), dict) else {}
    if any(k in params for k in ("median", "mu", "mean", "single_losses")) and "currency" not in params:
        warnings.append(
            ValidationMessage(
                level="warning",
                source="semantic",
                path="scenario -> severity -> parameters",
                message="Severity node has monetary values but no 'currency' property. Specify the currency to avoid implicit assumptions.",
            )
        )

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
        schema = _load_scenario_schema()
    except FileNotFoundError:
        return ValidationReport(
            ok=False,
            errors=[
                ValidationMessage(
                    level="error",
                    source="io",
                    path="(root)",
                    message=f"Schema file not found at {SCENARIO_SCHEMA_PATH}",
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

    warnings = _semantic_warnings(data) if not errors else []

    if strict_model and not errors:
        try:
            from ..models.crml_model import CRScenarioSchema

            CRScenarioSchema.model_validate(data)
        except Exception as e:
            try:
                pydantic_errors = e.errors()  # type: ignore[attr-defined]
            except Exception:
                pydantic_errors = None

            if isinstance(pydantic_errors, list):
                for pe in pydantic_errors:
                    loc = pe.get("loc", ())
                    path = " -> ".join(map(str, loc)) if loc else "(root)"
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
                        path="(root)",
                        message=f"Pydantic validation failed: {e}",
                        validator="pydantic",
                    )
                )

    return ValidationReport(ok=(len(errors) == 0), errors=errors, warnings=warnings)
