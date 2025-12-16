from __future__ import annotations

from typing import Any, Literal
import os

from jsonschema import Draft202012Validator

from .common import (
    ValidationMessage,
    ValidationReport,
    PORTFOLIO_SCHEMA_PATH,
    _load_input,
    _load_portfolio_schema,
    _jsonschema_path,
    _format_jsonschema_error,
    _control_ids_from_controls,
)
from .control_catalog import validate_control_catalog
from .control_assessment import validate_control_assessment


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

    def _resolve_path(p: str) -> str:
        if base_dir and not os.path.isabs(p):
            return os.path.join(base_dir, p)
        return p

    # Optional pack references: load/validate catalogs + assessments.
    catalog_paths: list[str] = []
    assessment_paths: list[str] = []

    catalog_sources = portfolio.get("control_catalogs")
    if catalog_sources is not None:
        if not isinstance(catalog_sources, list):
            messages.append(
                ValidationMessage(
                    level="error",
                    source="semantic",
                    path="portfolio -> control_catalogs",
                    message="portfolio.control_catalogs must be a list of file paths.",
                )
            )
        else:
            for idx, p in enumerate(catalog_sources):
                if not isinstance(p, str) or not p:
                    messages.append(
                        ValidationMessage(
                            level="error",
                            source="semantic",
                            path=f"portfolio -> control_catalogs -> {idx}",
                            message="control catalog path must be a non-empty string.",
                        )
                    )
                    continue

                resolved = _resolve_path(p)
                catalog_paths.append(resolved)

                if not os.path.exists(resolved):
                    messages.append(
                        ValidationMessage(
                            level="error",
                            source="semantic",
                            path=f"portfolio -> control_catalogs -> {idx}",
                            message=f"Control catalog file not found at path: {resolved}",
                        )
                    )
                    continue

                cat_report = validate_control_catalog(resolved, source_kind="path")
                if not cat_report.ok:
                    for e in cat_report.errors:
                        messages.append(
                            ValidationMessage(
                                level=e.level,
                                source=e.source,
                                path=f"portfolio -> control_catalogs -> {idx} -> {e.path}",
                                message=e.message,
                                validator=e.validator,
                            )
                        )

    assessment_sources = portfolio.get("control_assessments")
    if assessment_sources is not None:
        if not isinstance(assessment_sources, list):
            messages.append(
                ValidationMessage(
                    level="error",
                    source="semantic",
                    path="portfolio -> control_assessments",
                    message="portfolio.control_assessments must be a list of file paths.",
                )
            )
        else:
            for idx, p in enumerate(assessment_sources):
                if not isinstance(p, str) or not p:
                    messages.append(
                        ValidationMessage(
                            level="error",
                            source="semantic",
                            path=f"portfolio -> control_assessments -> {idx}",
                            message="control assessment path must be a non-empty string.",
                        )
                    )
                    continue

                resolved = _resolve_path(p)
                assessment_paths.append(resolved)

                if not os.path.exists(resolved):
                    messages.append(
                        ValidationMessage(
                            level="error",
                            source="semantic",
                            path=f"portfolio -> control_assessments -> {idx}",
                            message=f"Control assessment file not found at path: {resolved}",
                        )
                    )
                    continue

                assess_report = validate_control_assessment(
                    resolved,
                    source_kind="path",
                    control_catalogs=catalog_paths if catalog_paths else None,
                    control_catalogs_source_kind="path",
                )
                if not assess_report.ok:
                    for e in assess_report.errors:
                        messages.append(
                            ValidationMessage(
                                level=e.level,
                                source=e.source,
                                path=f"portfolio -> control_assessments -> {idx} -> {e.path}",
                                message=e.message,
                                validator=e.validator,
                            )
                        )

    # Build a catalog-id set (if any catalogs validated) for additional checks.
    catalog_ids: set[str] = set()
    if catalog_paths:
        for p in catalog_paths:
            cat_data, cat_io_errors = _load_input(p, source_kind="path")
            if cat_io_errors or not cat_data:
                continue
            catalog = cat_data.get("catalog")
            controls_any = catalog.get("controls") if isinstance(catalog, dict) else None
            if isinstance(controls_any, list):
                for entry in controls_any:
                    if isinstance(entry, dict) and isinstance(entry.get("id"), str):
                        catalog_ids.add(entry["id"])

    # Derive control ids from assessment packs (if any assessments validated).
    assessment_ids: set[str] = set()
    if assessment_paths:
        for p in assessment_paths:
            assess_data, assess_io_errors = _load_input(p, source_kind="path")
            if assess_io_errors or not assess_data:
                continue
            assessment = assess_data.get("assessment")
            assessments_any = assessment.get("assessments") if isinstance(assessment, dict) else None
            if isinstance(assessments_any, list):
                for entry in assessments_any:
                    if isinstance(entry, dict) and isinstance(entry.get("id"), str):
                        assessment_ids.add(entry["id"])

    # Collect IDs / paths
    scenario_ids: list[str] = []
    scenario_paths: list[str] = []

    for sc in scenarios:
        if not isinstance(sc, dict):
            continue

        sid = sc.get("id")
        if isinstance(sid, str):
            scenario_ids.append(sid)

        spath = sc.get("path")
        if isinstance(spath, str):
            scenario_paths.append(spath)

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
    if validate_scenarios:
        portfolio_controls = portfolio.get("controls")
        portfolio_control_ids: set[str] = set()
        if isinstance(portfolio_controls, list):
            for c in portfolio_controls:
                if isinstance(c, dict) and isinstance(c.get("id"), str):
                    portfolio_control_ids.add(c["id"])

        # If the portfolio does not provide explicit controls, fall back to the set of ids from assessments.
        using_assessment_controls = False
        if not portfolio_control_ids and assessment_ids:
            portfolio_control_ids = set(assessment_ids)
            using_assessment_controls = True

        # If a catalog is provided, require portfolio controls to exist in it.
        if catalog_ids and portfolio_control_ids:
            for cid in sorted(portfolio_control_ids):
                if cid not in catalog_ids:
                    messages.append(
                        ValidationMessage(
                            level="error",
                            source="semantic",
                            path="portfolio -> controls -> id",
                            message=f"Portfolio references unknown control id '{cid}' (not found in referenced control catalog pack(s)).",
                        )
                    )

        if using_assessment_controls:
            messages.append(
                ValidationMessage(
                    level="warning",
                    source="semantic",
                    path="portfolio -> controls",
                    message="portfolio.controls is missing/empty; using control ids from referenced control assessment pack(s) for scenario mapping.",
                )
            )

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

                from ..models.crml_model import CRScenarioSchema

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
                        message="Scenario(s) reference controls but no control inventory is available. Provide portfolio.controls or reference control_assessments.",
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
    """Validate a CRML portfolio document."""

    data, io_errors = _load_input(source, source_kind=source_kind)
    if io_errors:
        return ValidationReport(ok=False, errors=io_errors, warnings=[])
    assert data is not None

    try:
        schema = _load_portfolio_schema()
    except FileNotFoundError:
        return ValidationReport(
            ok=False,
            errors=[
                ValidationMessage(
                    level="error",
                    source="io",
                    path="(root)",
                    message=f"Schema file not found at {PORTFOLIO_SCHEMA_PATH}",
                )
            ],
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
