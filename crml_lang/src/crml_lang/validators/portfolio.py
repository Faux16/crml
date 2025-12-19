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
from .assessment import validate_assessment
from .control_relationships import validate_control_relationships


_PATH_PORTFOLIO_CONTROLS_ID = "portfolio -> controls -> id"
_PATH_PORTFOLIO_CONTROLS = "portfolio -> controls"


def _resolve_path(base_dir: str | None, p: str) -> str:
    """Resolve a possibly-relative path against `base_dir`."""
    if base_dir and not os.path.isabs(p):
        return os.path.join(base_dir, p)
    return p


def _norm_token(s: str) -> str:
    """Normalize a free-form token to a comparison-friendly form.

    Used for loose matching of industries/countries/framework names.
    """
    s = s.strip().lower()
    return "".join(ch for ch in s if ("a" <= ch <= "z") or ("0" <= ch <= "9") or ch in "_-" )


def _norm_list(v: Any) -> set[str]:
    """Normalize a list of strings into a set of normalized tokens."""
    if not isinstance(v, list):
        return set()
    out: set[str] = set()
    for item in v:
        if isinstance(item, str) and item.strip():
            out.add(_norm_token(item))
    return {x for x in out if x}


def _namespaces_from_control_ids(control_ids: set[str]) -> set[str]:
    """Extract normalized namespaces from canonical control ids (namespace:key)."""
    out: set[str] = set()
    for cid in control_ids:
        if not isinstance(cid, str):
            continue
        if ":" not in cid:
            continue
        ns = cid.split(":", 1)[0]
        ns_norm = _norm_token(ns)
        if ns_norm:
            out.add(ns_norm)
    return out


def _effective_portfolio_frameworks(
    *,
    declared_frameworks: set[str],
    catalog_ids: set[str],
    validate_relevance: bool,
) -> tuple[set[str], list[ValidationMessage]]:
    """Compute the effective portfolio framework set.

    If relevance validation is enabled, this can infer frameworks from referenced
    control catalogs, or error if declared frameworks don't cover catalog namespaces.
    """
    if not validate_relevance or not catalog_ids:
        return declared_frameworks, []

    catalog_namespaces = _namespaces_from_control_ids(catalog_ids)
    if not catalog_namespaces:
        return declared_frameworks, []

    if not declared_frameworks:
        inferred = set(catalog_namespaces)
        return (
            inferred,
            [
                ValidationMessage(
                    level="warning",
                    source="semantic",
                    path="meta -> regulatory_frameworks",
                    message=(
                        "meta.regulatory_frameworks is missing/empty; inferring it from referenced control catalog(s) "
                        f"as {sorted(inferred)}."
                    ),
                )
            ],
        )

    if not catalog_namespaces.issubset(declared_frameworks):
        missing = sorted(catalog_namespaces - declared_frameworks)
        return (
            declared_frameworks,
            [
                ValidationMessage(
                    level="error",
                    source="semantic",
                    path="meta -> regulatory_frameworks",
                    message=(
                        "meta.regulatory_frameworks does not include all framework namespaces implied by referenced control catalog(s). "
                        f"Missing: {missing}."
                    ),
                )
            ],
        )

    return declared_frameworks, []


def _require_catalogs_for_assessments(
    *,
    catalog_paths: list[str],
    assessment_paths: list[str],
) -> list[ValidationMessage]:
    """Require control catalogs when assessments are referenced.

    Assessments are validated against catalog control ids, so the catalog paths
    are required when assessment paths are present.
    """
    if not assessment_paths:
        return []
    if catalog_paths:
        return []
    return [
        ValidationMessage(
            level="error",
            source="semantic",
            path="portfolio -> control_catalogs",
            message=(
                "When portfolio.assessments is used, portfolio.control_catalogs must also be provided so assessment ids "
                "can be validated against a canonical control catalog."
            ),
        )
    ]


def _locale_countries(locale: Any) -> set[str]:
    """Extract a normalized set of countries from a locale object."""
    if not isinstance(locale, dict):
        return set()
    values: list[str] = []
    c = locale.get("country")
    if isinstance(c, str) and c.strip():
        values.append(c)
    cs = locale.get("countries")
    if isinstance(cs, list):
        for x in cs:
            if isinstance(x, str) and x.strip():
                values.append(x)

    out: set[str] = set()
    for x in values:
        token = _norm_token(x)
        if token:
            out.add(token)
    return out


def _controls_uniqueness_checks(portfolio: dict[str, Any]) -> list[ValidationMessage]:
    """Validate portfolio.controls entries have string ids and are unique."""
    messages: list[ValidationMessage] = []
    controls = portfolio.get("controls")
    if not isinstance(controls, list):
        return messages

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
                path=_PATH_PORTFOLIO_CONTROLS_ID,
                message="Control ids must be unique within a portfolio.",
            )
        )

    return messages


def _validate_catalog_and_assessment_references(
    *,
    portfolio: dict[str, Any],
    base_dir: str | None,
) -> tuple[list[str], list[str], list[ValidationMessage]]:
    """Validate catalog + assessment references and return resolved paths + messages."""
    catalog_paths, cat_messages = _validate_catalog_references(portfolio=portfolio, base_dir=base_dir)
    assessment_paths, assess_messages = _validate_assessment_references(
        portfolio=portfolio,
        base_dir=base_dir,
        catalog_paths=catalog_paths,
    )
    return catalog_paths, assessment_paths, [*cat_messages, *assess_messages]


def _validate_control_relationships_references(
    *,
    portfolio: dict[str, Any],
    base_dir: str | None,
) -> tuple[list[str], list[ValidationMessage]]:
    """Validate referenced control-relationships pack file paths and contents."""
    sources = portfolio.get("control_relationships")
    if sources is None:
        return [], []
    if not isinstance(sources, list):
        return (
            [],
            [
                ValidationMessage(
                    level="error",
                    source="semantic",
                    path="portfolio -> control_relationships",
                    message="portfolio.control_relationships must be a list of file paths.",
                )
            ],
        )

    paths: list[str] = []
    messages: list[ValidationMessage] = []
    for idx, p in enumerate(sources):
        if not isinstance(p, str) or not p:
            messages.append(
                ValidationMessage(
                    level="error",
                    source="semantic",
                    path=f"portfolio -> control_relationships -> {idx}",
                    message="control relationships pack path must be a non-empty string.",
                )
            )
            continue

        resolved = _resolve_path(base_dir, p)
        if not os.path.exists(resolved):
            messages.append(
                ValidationMessage(
                    level="error",
                    source="semantic",
                    path=f"portfolio -> control_relationships -> {idx}",
                    message=f"Control relationships file not found at path: {resolved}",
                )
            )
            paths.append(resolved)
            continue

        rel_report = validate_control_relationships(resolved, source_kind="path")
        if not rel_report.ok:
            for e in rel_report.errors:
                messages.append(
                    ValidationMessage(
                        level=e.level,
                        source=e.source,
                        path=f"portfolio -> control_relationships -> {idx} -> {e.path}",
                        message=e.message,
                        validator=e.validator,
                    )
                )

        paths.append(resolved)

    return paths, messages


def _validate_catalog_references(
    *,
    portfolio: dict[str, Any],
    base_dir: str | None,
) -> tuple[list[str], list[ValidationMessage]]:
    """Validate referenced control catalog file paths and return resolved paths."""
    sources = portfolio.get("control_catalogs")
    if sources is None:
        return [], []
    if not isinstance(sources, list):
        return (
            [],
            [
                ValidationMessage(
                    level="error",
                    source="semantic",
                    path="portfolio -> control_catalogs",
                    message="portfolio.control_catalogs must be a list of file paths.",
                )
            ],
        )

    paths: list[str] = []
    messages: list[ValidationMessage] = []
    for idx, p in enumerate(sources):
        resolved, entry_messages = _validate_one_catalog_path(p, idx=idx, base_dir=base_dir)
        messages.extend(entry_messages)
        if resolved is not None:
            paths.append(resolved)
    return paths, messages


def _validate_one_catalog_path(
    p: Any,
    *,
    idx: int,
    base_dir: str | None,
) -> tuple[str | None, list[ValidationMessage]]:
    """Validate one control catalog path entry and return (resolved_path, messages)."""
    messages: list[ValidationMessage] = []
    if not isinstance(p, str) or not p:
        return (
            None,
            [
                ValidationMessage(
                    level="error",
                    source="semantic",
                    path=f"portfolio -> control_catalogs -> {idx}",
                    message="control catalog path must be a non-empty string.",
                )
            ],
        )

    resolved = _resolve_path(base_dir, p)
    if not os.path.exists(resolved):
        messages.append(
            ValidationMessage(
                level="error",
                source="semantic",
                path=f"portfolio -> control_catalogs -> {idx}",
                message=f"Control catalog file not found at path: {resolved}",
            )
        )
        return resolved, messages

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

    return resolved, messages


def _validate_assessment_references(
    *,
    portfolio: dict[str, Any],
    base_dir: str | None,
    catalog_paths: list[str],
) -> tuple[list[str], list[ValidationMessage]]:
    """Validate referenced assessment file paths and (optionally) their contents."""
    sources = portfolio.get("assessments")
    if sources is None:
        return [], []
    if not isinstance(sources, list):
        return (
            [],
            [
                ValidationMessage(
                    level="error",
                    source="semantic",
                    path="portfolio -> assessments",
                    message="portfolio.assessments must be a list of file paths.",
                )
            ],
        )

    paths: list[str] = []
    messages: list[ValidationMessage] = []
    for idx, p in enumerate(sources):
        resolved, entry_messages = _validate_one_assessment_path(
            p,
            idx=idx,
            base_dir=base_dir,
            catalog_paths=catalog_paths,
        )
        messages.extend(entry_messages)
        if resolved is not None:
            paths.append(resolved)
    return paths, messages


def _validate_one_assessment_path(
    p: Any,
    *,
    idx: int,
    base_dir: str | None,
    catalog_paths: list[str],
) -> tuple[str | None, list[ValidationMessage]]:
    """Validate one assessment path entry and return (resolved_path, messages)."""
    if not isinstance(p, str) or not p:
        return (
            None,
            [
                ValidationMessage(
                    level="error",
                    source="semantic",
                    path=f"portfolio -> assessments -> {idx}",
                    message="assessment path must be a non-empty string.",
                )
            ],
        )

    resolved = _resolve_path(base_dir, p)
    if not os.path.exists(resolved):
        return (
            resolved,
            [
                ValidationMessage(
                    level="error",
                    source="semantic",
                    path=f"portfolio -> assessments -> {idx}",
                    message=f"Assessment file not found at path: {resolved}",
                )
            ],
        )

    assess_report = validate_assessment(
        resolved,
        source_kind="path",
        control_catalogs=catalog_paths if catalog_paths else None,
        control_catalogs_source_kind="path",
    )

    messages: list[ValidationMessage] = []
    if not assess_report.ok:
        for e in assess_report.errors:
            messages.append(
                ValidationMessage(
                    level=e.level,
                    source=e.source,
                    path=f"portfolio -> assessments -> {idx} -> {e.path}",
                    message=e.message,
                    validator=e.validator,
                )
            )

    return resolved, messages


def _catalog_ids_from_paths(catalog_paths: list[str]) -> set[str]:
    """Load referenced control catalogs and union their control ids."""
    out: set[str] = set()
    for p in catalog_paths:
        cat_data, cat_io_errors = _load_input(p, source_kind="path")
        if cat_io_errors or not cat_data:
            continue
        out |= _catalog_ids_from_data(cat_data)
    return out


def _catalog_ids_from_data(cat_data: dict[str, Any]) -> set[str]:
    """Extract control ids from a parsed control catalog document."""
    catalog = cat_data.get("catalog")
    controls_any = catalog.get("controls") if isinstance(catalog, dict) else None
    if not isinstance(controls_any, list):
        return set()
    return {entry["id"] for entry in controls_any if isinstance(entry, dict) and isinstance(entry.get("id"), str)}


def _assessment_ids_from_paths(assessment_paths: list[str]) -> set[str]:
    """Load referenced assessments and union their assessed control ids."""
    out: set[str] = set()
    for p in assessment_paths:
        assess_data, assess_io_errors = _load_input(p, source_kind="path")
        if assess_io_errors or not assess_data:
            continue
        out |= _assessment_ids_from_data(assess_data)
    return out


def _assessment_ids_from_data(assess_data: dict[str, Any]) -> set[str]:
    """Extract assessed control ids from a parsed assessment document."""
    assessment = assess_data.get("assessment")
    assessments_any = assessment.get("assessments") if isinstance(assessment, dict) else None
    if not isinstance(assessments_any, list):
        return set()
    return {entry["id"] for entry in assessments_any if isinstance(entry, dict) and isinstance(entry.get("id"), str)}


def _scenario_ids_paths(scenarios: list[Any]) -> tuple[list[str], list[str]]:
    """Extract scenario ids and scenario path strings from portfolio.scenarios."""
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
    return scenario_ids, scenario_paths


def _scenario_uniqueness_checks(scenario_ids: list[str], scenario_paths: list[str]) -> list[ValidationMessage]:
    """Ensure scenario ids and paths are unique within a portfolio."""
    messages: list[ValidationMessage] = []
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
    return messages


def _scenario_path_existence_checks(
    *,
    scenarios: list[Any],
    base_dir: str | None,
) -> list[ValidationMessage]:
    """Check that all referenced scenario paths exist on disk."""
    messages: list[ValidationMessage] = []
    for idx, sc in enumerate(scenarios):
        if not isinstance(sc, dict):
            continue
        spath = sc.get("path")
        if not isinstance(spath, str):
            continue
        resolved_path = _resolve_path(base_dir, spath)
        if not os.path.exists(resolved_path):
            messages.append(
                ValidationMessage(
                    level="error",
                    source="semantic",
                    path=f"portfolio -> scenarios -> {idx} -> path",
                    message=f"Scenario file not found at path: {resolved_path}",
                )
            )
    return messages


def _weight_semantic_checks(method: Any, scenarios: list[Any]) -> list[ValidationMessage]:
    """Validate portfolio scenario weights given a semantics method.

    For mixture/choose_one, requires weights and checks they sum to ~1.0.
    """
    messages: list[ValidationMessage] = []
    if method not in ("mixture", "choose_one"):
        return messages

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
                message=(
                    f"All scenarios must define 'weight' when portfolio.semantics.method is '{method}'. "
                    f"Missing at indices: {missing_weight_idx}"
                ),
            )
        )

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

    return messages


def _relationship_reference_checks(relationships: Any, scenario_ids: list[str]) -> list[ValidationMessage]:
    """Validate portfolio.relationships references only known scenario ids."""
    if not isinstance(relationships, list) or not scenario_ids:
        return []
    scenario_id_set = set(scenario_ids)
    messages: list[ValidationMessage] = []
    for idx, rel in enumerate(relationships):
        if not isinstance(rel, dict):
            continue
        messages.extend(_relationship_check_correlation(rel, idx=idx, scenario_id_set=scenario_id_set))
        messages.extend(_relationship_check_conditional(rel, idx=idx, scenario_id_set=scenario_id_set))
    return messages


def _relationship_check_correlation(
    rel: dict[str, Any],
    *,
    idx: int,
    scenario_id_set: set[str],
) -> list[ValidationMessage]:
    """Validate a correlation relationship's `between` ids exist in the portfolio."""
    if rel.get("type") != "correlation":
        return []
    between = rel.get("between")
    if not isinstance(between, list):
        return []
    messages: list[ValidationMessage] = []
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
    return messages


def _relationship_check_conditional(
    rel: dict[str, Any],
    *,
    idx: int,
    scenario_id_set: set[str],
) -> list[ValidationMessage]:
    """Validate a conditional relationship's `given`/`then` ids exist in the portfolio."""
    if rel.get("type") != "conditional":
        return []
    messages: list[ValidationMessage] = []
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


def _relevance_checks_for_scenario(
    *,
    portfolio_industries: set[str],
    portfolio_company_sizes: set[str],
    portfolio_frameworks: set[str],
    portfolio_countries: set[str],
    scenario_doc: Any,
    scenario_id: Any,
    idx: int,
) -> list[ValidationMessage]:
    """Validate that a referenced scenario is relevant to the portfolio (best-effort).

    Uses overlaps between portfolio meta fields (industries, company_sizes, frameworks, countries)
    and the loaded scenario's meta.
    """
    s_meta = scenario_doc.meta
    scenario_industries = _norm_list(s_meta.industries)
    scenario_company_sizes = _norm_list(s_meta.company_sizes)
    scenario_frameworks = _norm_list(s_meta.regulatory_frameworks)
    scenario_countries = _locale_countries(s_meta.locale)

    messages = _relevance_overlap_errors(
        portfolio_industries=portfolio_industries,
        portfolio_company_sizes=portfolio_company_sizes,
        portfolio_frameworks=portfolio_frameworks,
        portfolio_countries=portfolio_countries,
        scenario_industries=scenario_industries,
        scenario_company_sizes=scenario_company_sizes,
        scenario_frameworks=scenario_frameworks,
        scenario_countries=scenario_countries,
        scenario_id=scenario_id,
        idx=idx,
    )
    messages.extend(
        _relevance_control_namespace_warnings(
            scenario_doc=scenario_doc,
            scenario_frameworks=scenario_frameworks,
            scenario_id=scenario_id,
            idx=idx,
        )
    )
    return messages


def _relevance_overlap_errors(
    *,
    portfolio_industries: set[str],
    portfolio_company_sizes: set[str],
    portfolio_frameworks: set[str],
    portfolio_countries: set[str],
    scenario_industries: set[str],
    scenario_company_sizes: set[str],
    scenario_frameworks: set[str],
    scenario_countries: set[str],
    scenario_id: Any,
    idx: int,
) -> list[ValidationMessage]:
    """Return errors when portfolio/scenario relevance sets are disjoint."""
    def _mk(label: str, pset: set[str], sset: set[str]) -> ValidationMessage:
        return ValidationMessage(
            level="error",
            source="semantic",
            path=f"portfolio -> scenarios -> {idx} -> path",
            message=(
                f"Scenario '{scenario_id}' is not relevant for this portfolio based on {label}. "
                f"Portfolio has {sorted(pset)}, scenario declares {sorted(sset)}."
            ),
        )

    messages: list[ValidationMessage] = []
    if portfolio_industries and scenario_industries and portfolio_industries.isdisjoint(scenario_industries):
        messages.append(_mk("industries", portfolio_industries, scenario_industries))
    if portfolio_company_sizes and scenario_company_sizes and portfolio_company_sizes.isdisjoint(scenario_company_sizes):
        messages.append(_mk("company sizes", portfolio_company_sizes, scenario_company_sizes))
    if portfolio_frameworks and scenario_frameworks and portfolio_frameworks.isdisjoint(scenario_frameworks):
        messages.append(_mk("regulatory frameworks", portfolio_frameworks, scenario_frameworks))
    if portfolio_countries and scenario_countries and portfolio_countries.isdisjoint(scenario_countries):
        messages.append(_mk("countries", portfolio_countries, scenario_countries))
    return messages


def _relevance_control_namespace_warnings(
    *,
    scenario_doc: Any,
    scenario_frameworks: set[str],
    scenario_id: Any,
    idx: int,
) -> list[ValidationMessage]:
    """Warn if scenario control id namespaces are not declared in scenario frameworks."""
    if not scenario_frameworks:
        return []
    if not (scenario_doc.scenario.controls or []):
        return []
    messages: list[ValidationMessage] = []
    scenario_control_ids = _control_ids_from_controls(scenario_doc.scenario.controls or [])
    for cid in sorted(scenario_control_ids):
        ns = cid.split(":", 1)[0] if ":" in cid else ""
        ns_norm = _norm_token(ns)
        if ns_norm and ns_norm not in scenario_frameworks:
            messages.append(
                ValidationMessage(
                    level="warning",
                    source="semantic",
                    path=f"portfolio -> scenarios -> {idx} -> path",
                    message=(
                        f"Scenario '{scenario_id}' references control id '{cid}' with namespace '{ns}', "
                        "but scenario meta.regulatory_frameworks does not declare that namespace."
                    ),
                )
            )
    return messages


def _load_scenario_doc(resolved_path: str) -> tuple[Any | None, str | None]:
    """Load a scenario YAML file and validate it as a CRScenario.

    Returns:
        (scenario_doc, error_message). If loading/validation fails, scenario_doc is None.
    """
    try:
        import yaml

        with open(resolved_path, "r", encoding="utf-8") as f:
            scenario_data = yaml.safe_load(f)

        from ..models.scenario_model import CRScenario

        scenario_doc = CRScenario.model_validate(scenario_data)
        return scenario_doc, None
    except Exception as e:
        return None, str(e)


def _asset_cardinalities_by_name(portfolio: dict[str, Any]) -> dict[str, int]:
    """Build a mapping from asset name to cardinality (exposure units)."""
    assets = portfolio.get("assets")
    if not isinstance(assets, list):
        return {}
    out: dict[str, int] = {}
    for a in assets:
        if not isinstance(a, dict):
            continue
        name = a.get("name")
        card = a.get("cardinality")
        if not isinstance(name, str) or not name:
            continue
        if not isinstance(card, int):
            continue
        out[name] = card
    return out


def _binding_applies_to_assets(sc: dict[str, Any]) -> tuple[bool, Any]:
    """Return (is_present, value) for scenario binding.applies_to_assets."""
    binding = sc.get("binding")
    if not isinstance(binding, dict):
        return False, None
    if "applies_to_assets" not in binding:
        return False, None
    return True, binding.get("applies_to_assets")


def _bound_assets_from_binding(*, applies_present: bool, applies_value: Any, asset_cardinalities: dict[str, int]) -> list[str]:
    """Compute which assets are bound by a scenario entry.

    If applies_to_assets is missing/null, this defaults to all assets.
    """
    if not asset_cardinalities:
        return []
    if not applies_present or applies_value is None:
        return list(asset_cardinalities.keys())
    if isinstance(applies_value, list):
        return [x for x in applies_value if isinstance(x, str)]
    return []


def _total_exposure(bound_assets: list[str], asset_cardinalities: dict[str, int]) -> int:
    """Compute total exposure $E$ as the sum of cardinalities of bound assets."""
    return int(sum(int(asset_cardinalities.get(name, 0) or 0) for name in bound_assets))


def _frequency_binding_warnings(
    *,
    sc: dict[str, Any],
    scenario_doc: Any,
    idx: int,
    asset_cardinalities: dict[str, int],
) -> list[ValidationMessage]:
    """Language-level validation guidance for portfolio scenario bindings.

    - If frequency basis is per_asset_unit_per_year and total bound exposure E=0, warn.
    - If basis is per_organization_per_year and applies_to_assets is explicitly provided (non-null), warn.
    """

    try:
        basis = scenario_doc.scenario.frequency.basis
    except Exception:
        return []

    applies_present, applies_value = _binding_applies_to_assets(sc)

    messages: list[ValidationMessage] = []

    if basis == "per_organization_per_year" and applies_present and applies_value is not None:
        messages.append(
            ValidationMessage(
                level="warning",
                source="semantic",
                path=f"portfolio -> scenarios -> {idx} -> binding -> applies_to_assets",
                message=(
                    "Scenario frequency basis is 'per_organization_per_year'; asset binding does not affect frequency scaling "
                    "(expected annual event count is not multiplied by exposure). "
                    "If you intended per-asset scaling, use 'per_asset_unit_per_year'."
                ),
            )
        )

    if basis == "per_asset_unit_per_year":
        bound_assets = _bound_assets_from_binding(
            applies_present=applies_present,
            applies_value=applies_value,
            asset_cardinalities=asset_cardinalities,
        )
        exposure = _total_exposure(bound_assets, asset_cardinalities)

        if exposure == 0:
            messages.append(
                ValidationMessage(
                    level="warning",
                    source="semantic",
                    path=f"portfolio -> scenarios -> {idx} -> binding -> applies_to_assets",
                    message=(
                        "Scenario frequency basis is 'per_asset_unit_per_year' but total bound exposure E=0 (no assets bound). "
                        "Add portfolio.assets and/or bind this scenario to one or more assets."
                    ),
                )
            )

    return messages


def _portfolio_control_namespace_alignment(
    *,
    portfolio_control_ids: set[str],
    portfolio_frameworks: set[str],
) -> list[ValidationMessage]:
    """Validate portfolio control id namespaces align with meta.regulatory_frameworks."""
    messages: list[ValidationMessage] = []
    if not portfolio_frameworks or not portfolio_control_ids:
        return messages
    for cid in sorted(portfolio_control_ids):
        ns = cid.split(":", 1)[0] if ":" in cid else ""
        ns_norm = _norm_token(ns)
        if ns_norm and ns_norm not in portfolio_frameworks:
            messages.append(
                ValidationMessage(
                    level="error",
                    source="semantic",
                    path=_PATH_PORTFOLIO_CONTROLS_ID,
                    message=(
                        f"Portfolio control id '{cid}' uses namespace '{ns}', but meta.regulatory_frameworks does not declare it. "
                        "Either add the framework namespace to meta.regulatory_frameworks or adjust the control ids."
                    ),
                )
            )
    return messages


def _scenario_control_mapping_checks(
    *,
    scenario_doc: Any,
    portfolio_control_ids: set[str],
    scenario_idx: int,
) -> list[ValidationMessage]:
    """Cross-check scenario control references against the portfolio control inventory."""
    messages: list[ValidationMessage] = []
    scenario_controls_any = scenario_doc.scenario.controls or []
    scenario_controls = _control_ids_from_controls(scenario_controls_any)
    if scenario_controls and not portfolio_control_ids:
        messages.append(
            ValidationMessage(
                level="error",
                source="semantic",
                path=_PATH_PORTFOLIO_CONTROLS,
                message=(
                    "Scenario(s) reference controls but no control inventory is available. "
                    "Provide portfolio.controls or reference assessments."
                ),
            )
        )
        return messages

    for cid in scenario_controls:
        if cid not in portfolio_control_ids:
            messages.append(
                ValidationMessage(
                    level="error",
                    source="semantic",
                    path=f"portfolio -> scenarios -> {scenario_idx} -> path",
                    message=(
                        f"Scenario references control id '{cid}' but it is not present in portfolio.controls. "
                        "Add it (e.g. implementation_effectiveness: 0.0) to make the mapping explicit."
                    ),
                )
            )

    return messages


def _cross_document_checks(
    *,
    scenarios: list[Any],
    base_dir: str | None,
    require_paths_exist: bool,
    validate_scenarios: bool,
    validate_relevance: bool,
    portfolio_industries: set[str],
    portfolio_company_sizes: set[str],
    portfolio_frameworks: set[str],
    portfolio_countries: set[str],
    portfolio: dict[str, Any],
    asset_cardinalities: dict[str, int],
    assessment_ids: set[str],
    catalog_ids: set[str],
) -> list[ValidationMessage]:
    """Run cross-document checks that require loading referenced scenario files."""
    portfolio_control_ids, using_assessment_controls = _effective_portfolio_control_ids(
        portfolio=portfolio,
        assessment_ids=assessment_ids,
    )

    messages: list[ValidationMessage] = []
    messages.extend(_validate_controls_exist_in_catalog(catalog_ids=catalog_ids, portfolio_control_ids=portfolio_control_ids))

    if validate_relevance:
        messages.extend(
            _portfolio_control_namespace_alignment(
                portfolio_control_ids=portfolio_control_ids,
                portfolio_frameworks=portfolio_frameworks,
            )
        )

    if using_assessment_controls:
        messages.append(
            ValidationMessage(
                level="warning",
                source="semantic",
                path=_PATH_PORTFOLIO_CONTROLS,
                message="portfolio.controls is missing/empty; using control ids from referenced assessment catalog(s) for scenario mapping.",
            )
        )

    messages.extend(
        _scenario_cross_checks(
            scenarios=scenarios,
            base_dir=base_dir,
            require_paths_exist=require_paths_exist,
            validate_scenarios=validate_scenarios,
            validate_relevance=validate_relevance,
            portfolio_industries=portfolio_industries,
            portfolio_company_sizes=portfolio_company_sizes,
            portfolio_frameworks=portfolio_frameworks,
            portfolio_countries=portfolio_countries,
            portfolio_control_ids=portfolio_control_ids,
            asset_cardinalities=asset_cardinalities,
        )
    )
    return messages


def _effective_portfolio_control_ids(
    *,
    portfolio: dict[str, Any],
    assessment_ids: set[str],
) -> tuple[set[str], bool]:
    """Determine the effective set of portfolio control ids.

    Prefers explicit portfolio.controls; falls back to assessment ids if present.
    Returns a tuple (control_ids, using_assessment_controls).
    """
    portfolio_controls = portfolio.get("controls")
    ids: set[str] = set()
    if isinstance(portfolio_controls, list):
        ids = {c["id"] for c in portfolio_controls if isinstance(c, dict) and isinstance(c.get("id"), str)}

    if ids:
        return ids, False
    if assessment_ids:
        return set(assessment_ids), True
    return set(), False


def _validate_controls_exist_in_catalog(
    *,
    catalog_ids: set[str],
    portfolio_control_ids: set[str],
) -> list[ValidationMessage]:
    """Validate that portfolio control ids are present in referenced control catalogs."""
    if not catalog_ids or not portfolio_control_ids:
        return []
    missing = [cid for cid in sorted(portfolio_control_ids) if cid not in catalog_ids]
    return [
        ValidationMessage(
            level="error",
            source="semantic",
            path=_PATH_PORTFOLIO_CONTROLS_ID,
            message=f"Portfolio references unknown control id '{cid}' (not found in referenced control catalog(s)).",
        )
        for cid in missing
    ]


def _scenario_cross_checks(
    *,
    scenarios: list[Any],
    base_dir: str | None,
    require_paths_exist: bool,
    validate_scenarios: bool,
    validate_relevance: bool,
    portfolio_industries: set[str],
    portfolio_company_sizes: set[str],
    portfolio_frameworks: set[str],
    portfolio_countries: set[str],
    portfolio_control_ids: set[str],
    asset_cardinalities: dict[str, int],
) -> list[ValidationMessage]:
    """Run per-scenario cross-document checks for portfolio.scenarios."""
    messages: list[ValidationMessage] = []
    for idx, sc in enumerate(scenarios):
        if not isinstance(sc, dict):
            continue
        entry_messages, stop = _scenario_cross_checks_one(
            sc,
            idx=idx,
            base_dir=base_dir,
            require_paths_exist=require_paths_exist,
            validate_scenarios=validate_scenarios,
            validate_relevance=validate_relevance,
            portfolio_industries=portfolio_industries,
            portfolio_company_sizes=portfolio_company_sizes,
            portfolio_frameworks=portfolio_frameworks,
            portfolio_countries=portfolio_countries,
            portfolio_control_ids=portfolio_control_ids,
            asset_cardinalities=asset_cardinalities,
        )
        messages.extend(entry_messages)
        if stop:
            break
    return messages


def _scenario_cross_checks_one(
    sc: dict[str, Any],
    *,
    idx: int,
    base_dir: str | None,
    require_paths_exist: bool,
    validate_scenarios: bool,
    validate_relevance: bool,
    portfolio_industries: set[str],
    portfolio_company_sizes: set[str],
    portfolio_frameworks: set[str],
    portfolio_countries: set[str],
    portfolio_control_ids: set[str],
    asset_cardinalities: dict[str, int],
) -> tuple[list[ValidationMessage], bool]:
    """Run cross-document checks for a single portfolio.scenarios entry.

    Returns:
        (messages, stop). stop is true when downstream checks should stop early
        (e.g. missing portfolio control inventory required for multiple scenarios).
    """
    spath = sc.get("path")
    if not isinstance(spath, str) or not spath:
        return [], False

    resolved_path = _resolve_path(base_dir, spath)
    if not os.path.exists(resolved_path):
        if require_paths_exist:
            return [], False
        return (
            [
                ValidationMessage(
                    level="warning",
                    source="semantic",
                    path=f"portfolio -> scenarios -> {idx} -> path",
                    message=f"Cannot load scenario document for cross-document checks because file was not found at path: {resolved_path}",
                )
            ],
            False,
        )

    scenario_doc, load_error = _load_scenario_doc(resolved_path)
    if scenario_doc is None:
        return (
            [
                ValidationMessage(
                    level="error",
                    source="semantic",
                    path=f"portfolio -> scenarios -> {idx} -> path",
                    message=f"Failed to load/validate scenario for cross-document checks: {load_error}",
                )
            ],
            False,
        )

    messages: list[ValidationMessage] = []

    messages.extend(
        _frequency_binding_warnings(
            sc=sc,
            scenario_doc=scenario_doc,
            idx=idx,
            asset_cardinalities=asset_cardinalities,
        )
    )

    if validate_relevance:
        messages.extend(
            _relevance_checks_for_scenario(
                portfolio_industries=portfolio_industries,
                portfolio_company_sizes=portfolio_company_sizes,
                portfolio_frameworks=portfolio_frameworks,
                portfolio_countries=portfolio_countries,
                scenario_doc=scenario_doc,
                scenario_id=sc.get("id"),
                idx=idx,
            )
        )

    stop = False
    if validate_scenarios:
        messages.extend(
            _scenario_control_mapping_checks(
                scenario_doc=scenario_doc,
                portfolio_control_ids=portfolio_control_ids,
                scenario_idx=idx,
            )
        )
        stop = any(m.level == "error" and m.path == _PATH_PORTFOLIO_CONTROLS for m in messages)

    return messages, stop


def _portfolio_semantic_checks(data: dict[str, Any], *, base_dir: str | None = None) -> list[ValidationMessage]:
    """Run semantic validation checks for a portfolio document.

    These checks include uniqueness, reference integrity, weights, and optional
    cross-document checks controlled by portfolio.semantics.constraints.
    """
    messages: list[ValidationMessage] = []

    portfolio = data.get("portfolio")
    if not isinstance(portfolio, dict):
        return messages

    portfolio_meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
    portfolio_industries = _norm_list(portfolio_meta.get("industries"))
    portfolio_company_sizes = _norm_list(portfolio_meta.get("company_sizes"))
    portfolio_frameworks_declared = _norm_list(portfolio_meta.get("regulatory_frameworks"))
    portfolio_countries = _locale_countries(portfolio_meta.get("locale"))

    scenarios = portfolio.get("scenarios")
    if not isinstance(scenarios, list):
        return messages

    asset_cardinalities = _asset_cardinalities_by_name(portfolio)

    messages.extend(_controls_uniqueness_checks(portfolio))

    semantics = portfolio.get("semantics")
    if not isinstance(semantics, dict):
        return messages

    method = semantics.get("method")
    constraints = semantics.get("constraints") if isinstance(semantics.get("constraints"), dict) else {}

    validate_scenarios = isinstance(constraints, dict) and constraints.get("validate_scenarios") is True
    require_paths_exist = isinstance(constraints, dict) and constraints.get("require_paths_exist") is True
    validate_relevance = isinstance(constraints, dict) and constraints.get("validate_relevance") is True

    catalog_paths, assessment_paths, catalog_messages = _validate_catalog_and_assessment_references(
        portfolio=portfolio,
        base_dir=base_dir,
    )
    messages.extend(catalog_messages)

    _, relationship_messages = _validate_control_relationships_references(
        portfolio=portfolio,
        base_dir=base_dir,
    )
    messages.extend(relationship_messages)

    messages.extend(
        _require_catalogs_for_assessments(
            catalog_paths=catalog_paths,
            assessment_paths=assessment_paths,
        )
    )

    catalog_ids = _catalog_ids_from_paths(catalog_paths)
    assessment_ids = _assessment_ids_from_paths(assessment_paths)

    portfolio_frameworks, fw_messages = _effective_portfolio_frameworks(
        declared_frameworks=portfolio_frameworks_declared,
        catalog_ids=catalog_ids,
        validate_relevance=validate_relevance,
    )
    messages.extend(fw_messages)

    scenario_ids, scenario_paths = _scenario_ids_paths(scenarios)
    messages.extend(_scenario_uniqueness_checks(scenario_ids, scenario_paths))

    if require_paths_exist:
        messages.extend(_scenario_path_existence_checks(scenarios=scenarios, base_dir=base_dir))

    if validate_scenarios or validate_relevance:
        messages.extend(
            _cross_document_checks(
                scenarios=scenarios,
                base_dir=base_dir,
                require_paths_exist=require_paths_exist,
                validate_scenarios=validate_scenarios,
                validate_relevance=validate_relevance,
                portfolio_industries=portfolio_industries,
                portfolio_company_sizes=portfolio_company_sizes,
                portfolio_frameworks=portfolio_frameworks,
                portfolio_countries=portfolio_countries,
                portfolio=portfolio,
                asset_cardinalities=asset_cardinalities,
                assessment_ids=assessment_ids,
                catalog_ids=catalog_ids,
            )
        )

    messages.extend(_weight_semantic_checks(method, scenarios))

    messages.extend(_relationship_reference_checks(portfolio.get("relationships"), scenario_ids))

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
