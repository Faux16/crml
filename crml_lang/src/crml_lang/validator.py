"""CRML JSON Schema validator.

This module provides programmatic, structured validation APIs for CRML documents.

Design goals:
- Library-first API: functions return structured results and do not print.
- Flexible inputs: validate from a file path, a YAML string, or an in-memory dict.
- Spec contract: JSON Schema (Draft 2020-12) is the primary validation surface.
- Optional runtime check: opt-in Pydantic validation can be enabled to ensure the
  reference runtime model can parse the document.

Usage examples
--------------

Validate a file path (typical CLI/library usage)::

    from crml_lang import validate

    report = validate("model.yaml", source_kind="path")
    if not report.ok:
        # Structured access
        for err in report.errors:
            print(err.path, err.message)

Validate YAML content from a string::

    from crml_lang import validate

    yaml_text = '''
    crml: "1.1"
    meta: {name: "example"}
    model: {assets: [{name: "Servers", cardinality: 10}], frequency: {model: poisson, parameters: {lambda: 0.5}}, severity: {model: lognormal, parameters: {mu: 10, sigma: 1}}}
    '''
    report = validate(yaml_text, source_kind="yaml")
    print(report.ok)

Validate already-parsed data (dict)::

    from crml_lang import validate

    data = {"crml": "1.1", "meta": {"name": "example"}, "model": {"assets": [{"name": "Servers", "cardinality": 10}], "frequency": {"model": "poisson", "parameters": {"lambda": 0.5}}, "severity": {"model": "lognormal", "parameters": {"mu": 10, "sigma": 1}}}}
    report = validate(data, source_kind="data")

Enable strict runtime-model validation (optional)::

    report = validate("model.yaml", source_kind="path", strict_model=True)
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any, Literal, Optional

from jsonschema import Draft202012Validator


CRML_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schemas", "crml-scenario-schema.json")
PORTFOLIO_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schemas", "crml-portfolio-schema.json")
CONTROL_ASSESSMENT_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schemas", "crml-control-assessment-schema.json")


@dataclass(frozen=True)
class ValidationMessage:
    """A single validation message (error or warning)."""

    level: Literal["error", "warning"]
    message: str
    path: str = "(root)"
    source: Literal["schema", "semantic", "pydantic", "io"] = "schema"
    validator: Optional[str] = None


@dataclass(frozen=True)
class ValidationReport:
    """Structured validation output.

    Attributes:
        ok:
            True if schema validation passed (no errors). Warnings do not affect
            `ok`.
        errors:
            List of schema/model/IO errors.
                                message=f"Scenario references control id '{cid}' but it is not present in portfolio.controls. Add it (e.g. implementation_effectiveness: 0.0) to make the mapping explicit.",
            List of semantic warnings.
    """

    ok: bool
    errors: list[ValidationMessage]
    warnings: list[ValidationMessage]

    def render_text(self, *, source_label: Optional[str] = None) -> str:
        """Render a human-friendly validation summary (used by the CLI)."""

        label = source_label or "(input)"
        lines: list[str] = []

        if self.ok:
            lines.append(f"[OK] {label} is a valid CRML document.")
            for w in self.warnings:
                lines.append(f"[WARNING] {w.message}")
            return "\n".join(lines)

        lines.append(f"[ERROR] {label} failed CRML validation with {len(self.errors)} error(s):")
        for i, e in enumerate(self.errors, 1):
            lines.append(f"  {i}. [{e.path}] {e.message}")
        for w in self.warnings:
            lines.append(f"[WARNING] {w.message}")
        return "\n".join(lines)


def _load_schema(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_crml_schema() -> dict[str, Any]:
    return _load_schema(CRML_SCHEMA_PATH)


def _load_portfolio_schema() -> dict[str, Any]:
    return _load_schema(PORTFOLIO_SCHEMA_PATH)


def _load_control_assessment_schema() -> dict[str, Any]:
    return _load_schema(CONTROL_ASSESSMENT_SCHEMA_PATH)


def _looks_like_yaml_text(s: str) -> bool:
    # Heuristic: YAML documents almost always contain either newlines or
    # key separators. Callers can override via `source_kind`.
    return "\n" in s or ":" in s


def _load_input(
    source: str | dict[str, Any],
    *,
    source_kind: Literal["path", "yaml", "data"] | None,
) -> tuple[Optional[dict[str, Any]], list[ValidationMessage]]:
    errors: list[ValidationMessage] = []

    if source_kind == "data" or isinstance(source, dict):
        if not isinstance(source, dict):
            return None, [ValidationMessage(level="error", source="io", path="(root)", message="Expected a dict for source_kind='data'.")]
        return source, errors

    if not isinstance(source, str):
        return None, [ValidationMessage(level="error", source="io", path="(root)", message=f"Unsupported source type: {type(source).__name__}")]

    if source_kind == "path" or (source_kind is None and (os.path.exists(source) or not _looks_like_yaml_text(source))):
        if not os.path.exists(source):
            return None, [ValidationMessage(level="error", source="io", path="(root)", message=f"File not found: {source}")]
        try:
            with open(source, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            return None, [ValidationMessage(level="error", source="io", path="(root)", message=f"Failed to read file {source}: {e}")]
    else:
        text = source

    try:
        import yaml
    except Exception as e:
        return None, [ValidationMessage(level="error", source="io", path="(root)", message="PyYAML is required to parse YAML: pip install pyyaml")]

    try:
        data = yaml.safe_load(text)
    except Exception as e:
        return None, [ValidationMessage(level="error", source="io", path="(root)", message=f"Failed to parse YAML: {e}")]

    if not isinstance(data, dict):
        return None, [ValidationMessage(level="error", source="io", path="(root)", message="CRML document must parse to a YAML mapping (object/dict) at the root.")]

    return data, errors


def _jsonschema_path(error) -> str:
    try:
        if error.path:
            return " -> ".join(map(str, error.path))
    except Exception:
        pass
    return "(root)"


def _format_jsonschema_error(error) -> str:
    # Provide human-friendly error messages (keeps parity with earlier CLI output).
    if getattr(error, "validator", None) == "const":
        return f"Expected '{error.validator_value}', got '{error.instance}'"

    if getattr(error, "validator", None) == "oneOf":
        instance = getattr(error, "instance", None)
        if isinstance(instance, dict):
            if "mu" in instance and "median" in instance:
                return "Cannot use both 'median' and 'mu'. Choose one (median is recommended)."
            if "single_losses" in instance and any(k in instance for k in ("median", "mu", "sigma")):
                return "When using 'single_losses', do not also set 'median', 'mu', or 'sigma'."
            if "single_losses" in instance:
                return "'single_losses' must be an array with at least 2 positive values. It replaces median/mu/sigma by auto-calibration."
        return error.message

    if getattr(error, "validator", None) == "required":
        missing = None
        try:
            missing = error.validator_value[0]
        except Exception:
            pass
        if missing:
            return f"Missing required property: '{missing}'"
        return error.message

    if getattr(error, "validator", None) == "enum":
        try:
            values = ", ".join(map(str, error.validator_value))
            return f"Value must be one of: {values}"
        except Exception:
            return error.message

    return error.message


def _control_ids_from_controls(value: Any) -> list[str]:
    """Normalize control references to a list of control ids.

    Supports:
    - strings ("iso27001:2022:A.5.1")
    - dicts ({id: "...", ...})
    - Pydantic models with an `id` attribute
    """

    if not isinstance(value, list):
        return []

    ids: list[str] = []
    for item in value:
        if isinstance(item, str):
            ids.append(item)
            continue

        if isinstance(item, dict) and isinstance(item.get("id"), str):
            ids.append(item["id"])
            continue

        cid = getattr(item, "id", None)
        if isinstance(cid, str):
            ids.append(cid)

    return ids


def _semantic_warnings(data: dict[str, Any]) -> list[ValidationMessage]:
    warnings: list[ValidationMessage] = []

    # Warn if using old CRML version
    if data.get("crml_scenario") != "1.2":
        warnings.append(
            ValidationMessage(
                level="warning",
                source="semantic",
                path="crml_scenario",
                message=f"CRML scenario version '{data.get('crml_scenario')}' is not current. Consider upgrading to '1.2'.",
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

    # regions is inside meta.locale.regions
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

    # Warn if mixture weights don't sum to 1
    scenario = data.get("scenario", {}) if isinstance(data.get("scenario"), dict) else {}
    severity = scenario.get("severity", {}) if isinstance(scenario.get("severity"), dict) else {}
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
    """Validate a CRML document.

    Args:
        source:
            One of:
            - file path to a CRML YAML file
            - YAML content as a string
            - in-memory dict (already parsed)
        source_kind:
            Optional disambiguation for string inputs:
            - "path": treat `source` as a file path
            - "yaml": treat `source` as YAML text
            - "data": treat `source` as a dict
        strict_model:
            If True, additionally validates the document against the reference
            Pydantic runtime model (useful to catch spec/runtime drift).

    Returns:
        ValidationReport with `ok`, `errors`, and `warnings`.

    Examples:
        Validate a path::

            report = validate("model.yaml", source_kind="path")
            assert report.ok

        Validate YAML string::

            report = validate("crml: '1.1'\nmeta: {name: x}\nmodel: {...}", source_kind="yaml")

        Validate a dict::

            report = validate({"crml": "1.1", "meta": {"name": "x"}, "model": {...}}, source_kind="data")
    """

    data, io_errors = _load_input(source, source_kind=source_kind)
    if io_errors:
        return ValidationReport(ok=False, errors=io_errors, warnings=[])
    assert data is not None

    try:
        schema = _load_crml_schema()
    except FileNotFoundError:
        return ValidationReport(
            ok=False,
            errors=[ValidationMessage(level="error", source="io", path="(root)", message=f"Schema file not found at {CRML_SCHEMA_PATH}")],
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
            from .models.crml_model import CRScenarioSchema

            CRScenarioSchema.model_validate(data)
        except Exception as e:
            # Prefer detailed Pydantic errors if available.
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


def validate_control_assessment(
    source: str | dict[str, Any],
    *,
    source_kind: Literal["path", "yaml", "data"] | None = None,
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
            from .models.control_assessment_model import CRControlAssessmentSchema

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

    return ValidationReport(ok=(len(errors) == 0), errors=errors, warnings=[])


def _portfolio_semantic_checks(data: dict[str, Any], *, base_dir: str | None = None) -> list[ValidationMessage]:
    messages: list[ValidationMessage] = []

    portfolio = data.get("portfolio")
    if not isinstance(portfolio, dict):
        return messages

    scenarios = portfolio.get("scenarios")
    if not isinstance(scenarios, list):
        return messages

    # Controls uniqueness (by canonical id)
    controls = portfolio.get("controls")
    if isinstance(controls, list):
        ids: list[str] = []
        for idx, c in enumerate(controls):
            if not isinstance(c, dict):
                continue
            cid = c.get("id")
            if isinstance(cid, str):
                ids.append(cid)
            else:
                messages.append(
                    ValidationMessage(
                        level="error",
                        source="semantic",
                        path=f"portfolio -> controls -> {idx} -> id",
                        message="Control id must be a string.",
                    )
                )

        if len(ids) != len(set(ids)):
            messages.append(
                ValidationMessage(
                    level="error",
                    source="semantic",
                    path="portfolio -> controls -> id",
                    message="Control ids must be unique within a portfolio.",
                )
            )

    semantics = portfolio.get("semantics")
    if not isinstance(semantics, dict):
        return messages

    method = semantics.get("method")
    constraints = semantics.get("constraints") if isinstance(semantics.get("constraints"), dict) else {}

    validate_scenarios = isinstance(constraints, dict) and constraints.get("validate_scenarios") is True
    require_paths_exist = isinstance(constraints, dict) and constraints.get("require_paths_exist") is True

    # Collect IDs / paths
    scenario_ids: list[str] = []
    scenario_paths: list[str] = []
    weights: list[float] = []

    for idx, sc in enumerate(scenarios):
        if not isinstance(sc, dict):
            continue

        sid = sc.get("id")
        if isinstance(sid, str):
            scenario_ids.append(sid)

        spath = sc.get("path")
        if isinstance(spath, str):
            scenario_paths.append(spath)

        w = sc.get("weight")
        if w is None:
            continue
        try:
            weights.append(float(w))
        except Exception:
            messages.append(
                ValidationMessage(
                    level="error",
                    source="semantic",
                    path=f"portfolio -> scenarios -> {idx} -> weight",
                    message="Scenario weight must be a number.",
                )
            )

    # Uniqueness checks (JSON Schema cannot enforce unique-by-property)
    if len(set(scenario_ids)) != len(scenario_ids):
        messages.append(
            ValidationMessage(
                level="error",
                source="semantic",
                path="portfolio -> scenarios -> id",
                message="Scenario ids must be unique within a portfolio.",
            )
        )

    if len(set(scenario_paths)) != len(scenario_paths):
        messages.append(
            ValidationMessage(
                level="error",
                source="semantic",
                path="portfolio -> scenarios -> path",
                message="Scenario paths must be unique within a portfolio.",
            )
        )

    # Optional on-disk existence check for local paths (opt-in)
    if require_paths_exist:
        for idx, sc in enumerate(scenarios):
            if not isinstance(sc, dict):
                continue
            spath = sc.get("path")
            if not isinstance(spath, str):
                continue

            resolved_path = spath
            if base_dir and not os.path.isabs(resolved_path):
                resolved_path = os.path.join(base_dir, resolved_path)

            if not os.path.exists(resolved_path):
                messages.append(
                    ValidationMessage(
                        level="error",
                        source="semantic",
                        path=f"portfolio -> scenarios -> {idx} -> path",
                        message=f"Scenario file not found at path: {resolved_path}",
                    )
                )

    # Cross-document check: controls referenced by scenarios must be present in portfolio.controls.
    # This supports CRML Studio by producing a deterministic "controls to map" list.
    if validate_scenarios:
        portfolio_controls = portfolio.get("controls")
        portfolio_control_ids: set[str] = set()
        if isinstance(portfolio_controls, list):
            for c in portfolio_controls:
                if isinstance(c, dict) and isinstance(c.get("id"), str):
                    portfolio_control_ids.add(c["id"])

        for idx, sc in enumerate(scenarios):
            if not isinstance(sc, dict):
                continue

            spath = sc.get("path")
            if not isinstance(spath, str) or not spath:
                continue

            resolved_path = spath
            if base_dir and not os.path.isabs(resolved_path):
                resolved_path = os.path.join(base_dir, resolved_path)

            if not os.path.exists(resolved_path):
                # If required, missing files are already errors above; otherwise warn.
                if not require_paths_exist:
                    messages.append(
                        ValidationMessage(
                            level="warning",
                            source="semantic",
                            path=f"portfolio -> scenarios -> {idx} -> path",
                            message=f"Cannot verify scenario control mappings because scenario file was not found at path: {resolved_path}",
                        )
                    )
                continue

            try:
                import yaml

                with open(resolved_path, "r", encoding="utf-8") as f:
                    scenario_data = yaml.safe_load(f)

                from .models.crml_model import CRScenarioSchema

                scenario_doc = CRScenarioSchema.model_validate(scenario_data)
            except Exception as e:
                messages.append(
                    ValidationMessage(
                        level="error",
                        source="semantic",
                        path=f"portfolio -> scenarios -> {idx} -> path",
                        message=f"Failed to load/validate scenario for control mapping: {e}",
                    )
                )
                continue

            scenario_controls_any = scenario_doc.scenario.controls or []
            scenario_controls = _control_ids_from_controls(scenario_controls_any)
            if scenario_controls and not portfolio_control_ids:
                messages.append(
                    ValidationMessage(
                        level="error",
                        source="semantic",
                        path="portfolio -> controls",
                        message="Scenario(s) reference controls but portfolio.controls is missing or empty. Import your control assessment output into the portfolio.",
                    )
                )
                break

            for cid in scenario_controls:
                if cid not in portfolio_control_ids:
                    messages.append(
                        ValidationMessage(
                            level="error",
                            source="semantic",
                            path=f"portfolio -> scenarios -> {idx} -> path",
                            message=f"Scenario references control id '{cid}' but it is not present in portfolio.controls. Add it (e.g. implementation_effectiveness: 0.0) to make the mapping explicit.",
                        )
                    )

    # Weight semantics
    if method in ("mixture", "choose_one"):
        missing_weight_idx: list[int] = []
        for idx, sc in enumerate(scenarios):
            if not isinstance(sc, dict):
                continue
            if sc.get("weight") is None:
                missing_weight_idx.append(idx)
        if missing_weight_idx:
            messages.append(
                ValidationMessage(
                    level="error",
                    source="semantic",
                    path="portfolio -> scenarios",
                    message=f"All scenarios must define 'weight' when portfolio.semantics.method is '{method}'. Missing at indices: {missing_weight_idx}",
                )
            )

        # Sum-to-1 check
        try:
            weight_sum = 0.0
            for sc in scenarios:
                if isinstance(sc, dict) and sc.get("weight") is not None:
                    weight_sum += float(sc["weight"])

            if abs(weight_sum - 1.0) > 1e-9:
                messages.append(
                    ValidationMessage(
                        level="error",
                        source="semantic",
                        path="portfolio -> scenarios -> weight",
                        message=f"Scenario weights must sum to 1.0 for method '{method}' (got {weight_sum}).",
                    )
                )
        except Exception:
            # Numeric conversion errors are handled above per-scenario.
            pass

    # Relationship references must point to defined scenario ids
    relationships = portfolio.get("relationships")
    if isinstance(relationships, list) and scenario_ids:
        scenario_id_set = set(scenario_ids)
        for idx, rel in enumerate(relationships):
            if not isinstance(rel, dict):
                continue
            rel_type = rel.get("type")
            if rel_type == "correlation":
                between = rel.get("between")
                if isinstance(between, list):
                    for j, sid in enumerate(between):
                        if isinstance(sid, str) and sid not in scenario_id_set:
                            messages.append(
                                ValidationMessage(
                                    level="error",
                                    source="semantic",
                                    path=f"portfolio -> relationships -> {idx} -> between -> {j}",
                                    message=f"Unknown scenario id referenced in relationship: {sid}",
                                )
                            )

            if rel_type == "conditional":
                for key in ("given", "then"):
                    sid = rel.get(key)
                    if isinstance(sid, str) and sid not in scenario_id_set:
                        messages.append(
                            ValidationMessage(
                                level="error",
                                source="semantic",
                                path=f"portfolio -> relationships -> {idx} -> {key}",
                                message=f"Unknown scenario id referenced in relationship: {sid}",
                            )
                        )

    return messages


def validate_portfolio(
    source: str | dict[str, Any],
    *,
    source_kind: Literal["path", "yaml", "data"] | None = None,
) -> ValidationReport:
    """Validate a CRML portfolio document.

    A portfolio document links multiple single-scenario CRML files and defines
    machine-enforced aggregation semantics (e.g., mixture/choose_one weights).
    """

    data, io_errors = _load_input(source, source_kind=source_kind)
    if io_errors:
        return ValidationReport(ok=False, errors=io_errors, warnings=[])
    assert data is not None

    try:
        schema = _load_portfolio_schema()
    except FileNotFoundError:
        return ValidationReport(
            ok=False,
            errors=[ValidationMessage(level="error", source="io", path="(root)", message=f"Schema file not found at {PORTFOLIO_SCHEMA_PATH}")],
            warnings=[],
        )

    validator = Draft202012Validator(schema)
    errors: list[ValidationMessage] = []
    warnings: list[ValidationMessage] = []
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

    # Portfolio semantic checks are machine-enforced semantics, but may also produce warnings.
    if not errors:
        base_dir = None
        if isinstance(source, str) and source_kind == "path":
            base_dir = os.path.dirname(os.path.abspath(source))

        for msg in _portfolio_semantic_checks(data, base_dir=base_dir):
            if msg.level == "warning":
                warnings.append(msg)
            else:
                errors.append(msg)

    return ValidationReport(ok=(len(errors) == 0), errors=errors, warnings=warnings)
