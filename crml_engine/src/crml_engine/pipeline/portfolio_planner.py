from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Optional
import os

from pydantic import BaseModel, Field

from crml_lang.models.portfolio_bundle import CRPortfolioBundle
from crml_lang.models.portfolio_model import CRPortfolioSchema, Portfolio, ScenarioRef
from crml_lang.models.crml_model import CRScenarioSchema, ScenarioControl as ScenarioControlModel
from crml_lang.models.control_assessment_model import CRControlAssessmentSchema, ControlAssessment
from crml_lang.models.control_catalog_model import CRControlCatalogSchema


class PlanMessage(BaseModel):
    level: Literal["error", "warning"] = Field(..., description="Message severity level.")
    path: str = Field(..., description="Logical document path where the issue occurred.")
    message: str = Field(..., description="Human-readable message.")


class ResolvedScenarioControl(BaseModel):
    id: str = Field(..., description="Canonical control id.")

    # Inventory inputs (portfolio.controls, assessment packs)
    inventory_implementation_effectiveness: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Implementation effectiveness from inventory sources (0..1)."
    )
    inventory_coverage_value: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Coverage value from inventory sources (0..1)."
    )
    inventory_coverage_basis: Optional[str] = Field(
        None, description="Coverage basis from inventory sources (e.g. endpoints, employees)."
    )

    inventory_reliability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Reliability/uptime from inventory sources (0..1)."
    )
    affects: Optional[str] = Field(
        None, description="Effect surface for the control (frequency, severity, or both)."
    )

    # Scenario-scoped factors (optional)
    scenario_implementation_effectiveness_factor: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Scenario-scoped multiplier for implementation effectiveness (0..1)."
    )
    scenario_coverage_factor: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Scenario-scoped multiplier for coverage (0..1)."
    )
    scenario_coverage_basis: Optional[str] = Field(
        None, description="Scenario-scoped coverage basis override (if applicable)."
    )

    scenario_potency_factor: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description=(
            "Scenario-scoped potency factor for this control against this specific threat (0..1). "
            "This multiplies inventory implementation effectiveness when deriving combined values."
        ),
    )

    # Combined values (what the engine should apply)
    combined_implementation_effectiveness: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Combined implementation effectiveness to apply (0..1)."
    )
    combined_coverage_value: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Combined coverage value to apply (0..1)."
    )

    combined_reliability: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Combined reliability/uptime probability to apply (0..1)."
    )


class ResolvedScenario(BaseModel):
    id: str = Field(..., description="Scenario id from the portfolio.")
    path: str = Field(..., description="Scenario path from the portfolio.")
    resolved_path: Optional[str] = Field(None, description="Resolved absolute path for loading the scenario.")
    weight: Optional[float] = Field(None, description="Optional scenario weight (portfolio semantics dependent).")

    # Portfolio binding resolution
    applies_to_assets: list[str] = Field(
        default_factory=list,
        description="Concrete list of portfolio asset names this scenario applies to.",
    )
    cardinality: int = Field(..., ge=0, description="Total exposure cardinality implied by applies_to_assets.")

    # Scenario document metadata (useful for reporting)
    scenario_name: Optional[str] = Field(None, description="Scenario meta.name (if present).")

    # Resolved control effects for this scenario
    controls: list[ResolvedScenarioControl] = Field(
        default_factory=list,
        description="Resolved per-control effects applicable to this scenario.",
    )


class PortfolioExecutionPlan(BaseModel):
    # Copy-through metadata needed by the runtime
    portfolio_name: Optional[str] = Field(None, description="Portfolio meta.name (if present).")
    semantics_method: str = Field(..., description="Resolved portfolio aggregation method.")

    assets: list[dict[str, Any]] = Field(
        default_factory=list, description="Execution-ready asset payload (engine-defined structure)."
    )
    scenarios: list[ResolvedScenario] = Field(..., description="Resolved scenarios included in the plan.")
    dependency: Optional[dict[str, Any]] = Field(
        None, description="Optional execution-ready dependency payload (engine-defined structure)."
    )


def _is_control_state_ref(ref: str) -> bool:
    # Minimal v1: control:<id>:state
    if not isinstance(ref, str):
        return False
    if not ref.startswith("control:"):
        return False
    if not ref.endswith(":state"):
        return False
    middle = ref[len("control:") : -len(":state")]
    return bool(middle)


def _extract_control_id_from_state_ref(ref: str) -> str:
    return ref[len("control:") : -len(":state")]


def _toeplitz_corr(dim: int, rho: float) -> list[list[float]]:
    r = float(rho)
    return [[(r ** abs(i - j)) for j in range(dim)] for i in range(dim)]


def _validate_corr_matrix(matrix: list[list[float]], dim: int) -> Optional[str]:
    if len(matrix) != dim:
        return f"matrix must have {dim} rows"
    for i, row in enumerate(matrix):
        if not isinstance(row, list) or len(row) != dim:
            return f"matrix row {i} must have length {dim}"
        for j, v in enumerate(row):
            try:
                fv = float(v)
            except Exception:
                return f"matrix[{i}][{j}] must be a number"
            if i == j and abs(fv - 1.0) > 1e-9:
                return "matrix diagonal entries must be 1.0"
            if fv < -1.0 or fv > 1.0:
                return "matrix entries must be in [-1, 1]"
    # symmetry
    for i in range(dim):
        for j in range(i + 1, dim):
            if abs(float(matrix[i][j]) - float(matrix[j][i])) > 1e-9:
                return "matrix must be symmetric"
    return None


class PlanReport(BaseModel):
    ok: bool = Field(..., description="True if planning completed successfully.")
    errors: list[PlanMessage] = Field(default_factory=list, description="Errors encountered during planning.")
    warnings: list[PlanMessage] = Field(default_factory=list, description="Warnings encountered during planning.")
    plan: Optional[PortfolioExecutionPlan] = Field(
        None, description="Resolved execution plan (present only when ok is true)."
    )


def _load_yaml_file(path: str) -> dict[str, Any]:
    try:
        import yaml
    except Exception as e:
        raise ImportError("PyYAML is required: pip install pyyaml") from e

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError("YAML document must be a mapping/object at top-level")
    return data


def _resolve_path(base_dir: str | None, p: str) -> str:
    if base_dir and not os.path.isabs(p):
        return os.path.join(base_dir, p)
    return p


def _scenario_controls_to_objects(
    controls_any: list[Any],
) -> list[tuple[str, Optional[float], Optional[tuple[float, str]], Optional[float]]]:
    """Normalize scenario.controls into (id, eff_factor, coverage_factor(value,basis), potency_factor)."""

    out: list[tuple[str, Optional[float], Optional[tuple[float, str]], Optional[float]]] = []
    for c in controls_any:
        if isinstance(c, str):
            out.append((c, None, None, None))
            continue

        if isinstance(c, ScenarioControlModel):
            cov = None
            if c.coverage is not None:
                cov = (float(c.coverage.value), str(c.coverage.basis))
            out.append((c.id, c.implementation_effectiveness, cov, getattr(c, "potency", None)))
            continue

        if isinstance(c, dict):
            cid = c.get("id")
            if isinstance(cid, str):
                eff = c.get("implementation_effectiveness")
                eff_f = float(eff) if eff is not None else None
                pot = c.get("potency")
                pot_f = float(pot) if pot is not None else None
                cov_obj = c.get("coverage")
                cov = None
                if isinstance(cov_obj, dict) and cov_obj.get("value") is not None and cov_obj.get("basis") is not None:
                    cov = (float(cov_obj["value"]), str(cov_obj["basis"]))
                out.append((cid, eff_f, cov, pot_f))
            continue

    return out


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def _distinct_non_none(values: list[object]) -> set[object]:
    return {v for v in values if v is not None}


def plan_portfolio(
    source: str | dict[str, Any],
    *,
    source_kind: Literal["path", "yaml", "data"] = "path",
) -> PlanReport:
    """Resolve a CRML portfolio into an execution-friendly plan.

    This is intentionally *not* a simulator. It resolves:
    - portfolio asset bindings (applies_to_assets -> concrete exposures)
    - referenced scenario documents
    - referenced control packs (catalogs/assessments)
    - scenario control refs -> resolved, combined control effects

    The resulting plan is designed to be consumed by `crml_engine`.
    """

    errors: list[PlanMessage] = []
    warnings: list[PlanMessage] = []

    base_dir: str | None = None
    data: dict[str, Any]

    if source_kind == "path":
        assert isinstance(source, str)
        base_dir = os.path.dirname(os.path.abspath(source))
        try:
            data = _load_yaml_file(source)
        except Exception as e:
            return PlanReport(ok=False, errors=[PlanMessage(level="error", path="(io)", message=str(e))])
    elif source_kind == "yaml":
        assert isinstance(source, str)
        try:
            import yaml
        except Exception as e:
            raise ImportError("PyYAML is required: pip install pyyaml") from e
        loaded = yaml.safe_load(source)
        if not isinstance(loaded, dict):
            return PlanReport(ok=False, errors=[PlanMessage(level="error", path="(root)", message="YAML must be a mapping")])
        data = loaded
    else:
        assert isinstance(source, dict)
        data = source

    try:
        doc = CRPortfolioSchema.model_validate(data)
    except Exception as e:
        return PlanReport(ok=False, errors=[PlanMessage(level="error", path="(schema)", message=str(e))])

    portfolio: Portfolio = doc.portfolio

    assets_by_name: dict[str, Any] = {a.name: a for a in portfolio.assets}
    all_asset_names = list(assets_by_name.keys())

    # --- Load packs (optional) ---
    catalog_ids: set[str] = set()
    assessment_by_id: dict[str, ControlAssessment] = {}

    catalog_paths = [
        _resolve_path(base_dir, p)
        for p in (portfolio.control_catalogs or [])
        if isinstance(p, str) and p
    ]
    assessment_paths = [
        _resolve_path(base_dir, p)
        for p in (portfolio.control_assessments or [])
        if isinstance(p, str) and p
    ]

    for idx, p in enumerate(catalog_paths):
        if not os.path.exists(p):
            errors.append(PlanMessage(level="error", path=f"portfolio.control_catalogs[{idx}]", message=f"File not found: {p}"))
            continue
        try:
            cat_doc = CRControlCatalogSchema.model_validate(_load_yaml_file(p))
            for entry in cat_doc.catalog.controls:
                catalog_ids.add(entry.id)
        except Exception as e:
            errors.append(PlanMessage(level="error", path=f"portfolio.control_catalogs[{idx}]", message=f"Invalid control catalog pack: {e}"))

    for idx, p in enumerate(assessment_paths):
        if not os.path.exists(p):
            errors.append(PlanMessage(level="error", path=f"portfolio.control_assessments[{idx}]", message=f"File not found: {p}"))
            continue
        try:
            assess_doc = CRControlAssessmentSchema.model_validate(_load_yaml_file(p))
            for a in assess_doc.assessment.assessments:
                if a.id in assessment_by_id:
                    warnings.append(
                        PlanMessage(
                            level="warning",
                            path=f"portfolio.control_assessments[{idx}]",
                            message=f"Duplicate assessment for control id '{a.id}' across packs; last one wins.",
                        )
                    )
                assessment_by_id[a.id] = a
        except Exception as e:
            errors.append(PlanMessage(level="error", path=f"portfolio.control_assessments[{idx}]", message=f"Invalid control assessment pack: {e}"))

    # --- Build portfolio inventory (highest precedence) ---
    portfolio_controls_by_id: dict[str, Any] = {}
    for idx, c in enumerate(portfolio.controls or []):
        portfolio_controls_by_id[c.id] = c
        if catalog_ids and c.id not in catalog_ids:
            errors.append(
                PlanMessage(
                    level="error",
                    path=f"portfolio.controls[{idx}].id",
                    message=f"Unknown control id '{c.id}' (not present in referenced catalog pack(s)).",
                )
            )

    resolved_scenarios: list[ResolvedScenario] = []

    # --- Dependency normalization (optional) ---
    dependency_plan: Optional[dict[str, Any]] = None
    if portfolio.dependency is not None and portfolio.dependency.copula is not None:
        cop = portfolio.dependency.copula
        targets = list(cop.targets or [])
        dim = len(targets)
        bad_targets = [t for t in targets if not _is_control_state_ref(t)]
        if bad_targets:
            errors.append(
                PlanMessage(
                    level="error",
                    path="portfolio.dependency.copula.targets",
                    message=f"Unsupported target reference(s): {bad_targets}. Supported: control:<id>:state",
                )
            )
        else:
            target_control_ids = [_extract_control_id_from_state_ref(t) for t in targets]
            # Ensure targets exist in inventory or assessment packs (since scenario controls must resolve).
            for t in target_control_ids:
                if t not in portfolio_controls_by_id and t not in assessment_by_id:
                    errors.append(
                        PlanMessage(
                            level="error",
                            path="portfolio.dependency.copula.targets",
                            message=f"Copula target control id '{t}' not found in portfolio.controls or control assessments.",
                        )
                    )

            corr: Optional[list[list[float]]] = None
            if cop.matrix is not None:
                corr = [list(row) for row in cop.matrix]
            else:
                rho = cop.rho
                if cop.structure not in (None, "toeplitz"):
                    errors.append(
                        PlanMessage(
                            level="error",
                            path="portfolio.dependency.copula.structure",
                            message=f"Unsupported copula structure '{cop.structure}'.",
                        )
                    )
                if rho is None:
                    errors.append(
                        PlanMessage(
                            level="error",
                            path="portfolio.dependency.copula.rho",
                            message="Toeplitz copula requires 'rho' when 'matrix' is not provided.",
                        )
                    )
                else:
                    corr = _toeplitz_corr(dim=dim, rho=float(rho))

            if corr is not None:
                err = _validate_corr_matrix(corr, dim=dim)
                if err:
                    errors.append(
                        PlanMessage(
                            level="error",
                            path="portfolio.dependency.copula",
                            message=err,
                        )
                    )
                else:
                    dependency_plan = {
                        "copula": {
                            "type": cop.type,
                            "targets": targets,
                            "matrix": corr,
                        }
                    }

    for idx, sref in enumerate(portfolio.scenarios):
        assert isinstance(sref, ScenarioRef)
        scenario_path = _resolve_path(base_dir, sref.path)
        if not os.path.exists(scenario_path):
            errors.append(
                PlanMessage(
                    level="error",
                    path=f"portfolio.scenarios[{idx}].path",
                    message=f"Scenario file not found: {scenario_path}",
                )
            )
            continue

        try:
            scenario_doc = CRScenarioSchema.model_validate(_load_yaml_file(scenario_path))
        except Exception as e:
            errors.append(
                PlanMessage(
                    level="error",
                    path=f"portfolio.scenarios[{idx}].path",
                    message=f"Invalid scenario document: {e}",
                )
            )
            continue

        # Binding resolution
        applies_to_assets = sref.binding.applies_to_assets
        if applies_to_assets is None:
            applies_to_assets_list = list(all_asset_names)
        else:
            applies_to_assets_list = list(applies_to_assets)

        # Basis sanity checks (heuristic)
        basis = scenario_doc.scenario.frequency.basis
        if basis == "per_organization_per_year" and applies_to_assets is not None:
            warnings.append(
                PlanMessage(
                    level="warning",
                    path=f"portfolio.scenarios[{idx}].binding.applies_to_assets",
                    message=(
                        "Scenario frequency basis is 'per_organization_per_year'; asset binding does not affect cardinality (cardinality stays 1). "
                        "If you intended per-asset scaling, consider 'per_asset_unit_per_year'."
                    ),
                )
            )

        unknown_assets = [a for a in applies_to_assets_list if a not in assets_by_name]
        if unknown_assets:
            errors.append(
                PlanMessage(
                    level="error",
                    path=f"portfolio.scenarios[{idx}].binding.applies_to_assets",
                    message=f"Unknown asset(s) referenced: {unknown_assets}",
                )
            )
            continue

        # Cardinality
        if basis == "per_asset_unit_per_year":
            if not applies_to_assets_list:
                errors.append(
                    PlanMessage(
                        level="error",
                        path=f"portfolio.scenarios[{idx}].binding.applies_to_assets",
                        message="Scenario uses per_asset_unit_per_year but no assets are bound (empty applies_to_assets).",
                    )
                )
                continue
            cardinality = int(sum(int(assets_by_name[a].cardinality) for a in applies_to_assets_list))

            # Heuristic: very large exposure counts often violate linear-scaling assumptions.
            if cardinality >= 100_000:
                warnings.append(
                    PlanMessage(
                        level="warning",
                        path=f"portfolio.scenarios[{idx}]",
                        message=(
                            f"Scenario expands to total cardinality={cardinality} (per-asset-unit basis). "
                            "Linear scaling (cardinality × lambda) can be sensitive to correlation/shared-failure modes at large scales; "
                            "treat results as an approximation."
                        ),
                    )
                )

            # Heuristic: bound assets look heterogeneous; per-unit exchangeability may not hold.
            bound_assets = [assets_by_name[a] for a in applies_to_assets_list]

            distinct_tag_sets = _distinct_non_none([
                tuple(sorted(set(a.tags or []))) if (a.tags is not None) else None
                for a in bound_assets
            ])
            distinct_crit_types = _distinct_non_none([
                (a.criticality_index.type if a.criticality_index is not None else None)
                for a in bound_assets
            ])

            if len(distinct_tag_sets) > 1 or len(distinct_crit_types) > 1:
                warnings.append(
                    PlanMessage(
                        level="warning",
                        path=f"portfolio.scenarios[{idx}].binding.applies_to_assets",
                        message=(
                            "Bound assets appear heterogeneous (different tags and/or criticality_index.type). "
                            "Summed-cardinality scaling assumes comparable/exchangeable exposure units; consider splitting scenarios or modeling heterogeneity explicitly."
                        ),
                    )
                )
        else:
            cardinality = 1

        # Controls
        controls_any = scenario_doc.scenario.controls or []
        controls_norm = _scenario_controls_to_objects(list(controls_any))
        resolved_controls: list[ResolvedScenarioControl] = []

        for (cid, scenario_eff_factor, scenario_cov_factor, scenario_potency_factor) in controls_norm:
            inventory_eff: Optional[float] = None
            inventory_cov_val: Optional[float] = None
            inventory_cov_basis: Optional[str] = None
            inventory_rel: Optional[float] = None
            affects: Optional[str] = None

            inv = portfolio_controls_by_id.get(cid)
            if inv is not None:
                if inv.implementation_effectiveness is not None:
                    inventory_eff = float(inv.implementation_effectiveness)
                if inv.coverage is not None:
                    inventory_cov_val = float(inv.coverage.value)
                    inventory_cov_basis = str(inv.coverage.basis)
                if getattr(inv, "reliability", None) is not None:
                    inventory_rel = float(inv.reliability)
                if getattr(inv, "affects", None) is not None:
                    affects = str(inv.affects)
            else:
                assess = assessment_by_id.get(cid)
                if assess is not None:
                    if assess.implementation_effectiveness is not None:
                        inventory_eff = float(assess.implementation_effectiveness)
                    if assess.coverage is not None:
                        inventory_cov_val = float(assess.coverage.value)
                        inventory_cov_basis = str(assess.coverage.basis)
                    if getattr(assess, "reliability", None) is not None:
                        inventory_rel = float(assess.reliability)
                    if getattr(assess, "affects", None) is not None:
                        affects = str(assess.affects)

            if inventory_eff is None and inventory_cov_val is None:
                errors.append(
                    PlanMessage(
                        level="error",
                        path=f"portfolio.scenarios[{idx}].path",
                        message=f"Scenario references control id '{cid}' but no inventory/assessment data is available for it.",
                    )
                )
                continue

            # Scenario values are interpreted as *multiplicative applicability factors*.
            eff_factor = float(scenario_eff_factor) if scenario_eff_factor is not None else None
            pot_factor = float(scenario_potency_factor) if scenario_potency_factor is not None else None
            cov_factor_val: Optional[float] = None
            cov_factor_basis: Optional[str] = None
            if scenario_cov_factor is not None:
                cov_factor_val = float(scenario_cov_factor[0])
                cov_factor_basis = str(scenario_cov_factor[1])

            combined_eff = None
            if inventory_eff is not None:
                combined_eff = _clamp01(
                    inventory_eff
                    * (eff_factor if eff_factor is not None else 1.0)
                    * (pot_factor if pot_factor is not None else 1.0)
                )

            combined_cov = None
            if inventory_cov_val is not None:
                combined_cov = _clamp01(inventory_cov_val * (cov_factor_val if cov_factor_val is not None else 1.0))

            combined_rel = _clamp01(inventory_rel if inventory_rel is not None else 1.0)

            resolved_controls.append(
                ResolvedScenarioControl(
                    id=cid,
                    inventory_implementation_effectiveness=inventory_eff,
                    inventory_coverage_value=inventory_cov_val,
                    inventory_coverage_basis=inventory_cov_basis,
                    inventory_reliability=inventory_rel,
                    affects=affects,
                    scenario_implementation_effectiveness_factor=eff_factor,
                    scenario_coverage_factor=cov_factor_val,
                    scenario_coverage_basis=cov_factor_basis,
                    scenario_potency_factor=pot_factor,
                    combined_implementation_effectiveness=combined_eff,
                    combined_coverage_value=combined_cov,
                    combined_reliability=combined_rel,
                )
            )

            if inventory_cov_basis and cov_factor_basis and inventory_cov_basis != cov_factor_basis:
                warnings.append(
                    PlanMessage(
                        level="warning",
                        path=f"portfolio.scenarios[{idx}].path",
                        message=(
                            f"Control '{cid}' combines coverage with different bases: inventory='{inventory_cov_basis}', scenario='{cov_factor_basis}'. "
                            "Treating scenario coverage as a pure factor."
                        ),
                    )
                )

        resolved_scenarios.append(
            ResolvedScenario(
                id=sref.id,
                path=sref.path,
                resolved_path=scenario_path,
                weight=sref.weight,
                applies_to_assets=applies_to_assets_list,
                cardinality=cardinality,
                scenario_name=scenario_doc.meta.name,
                controls=resolved_controls,
            )
        )

    if errors:
        return PlanReport(ok=False, errors=errors, warnings=warnings, plan=None)

    plan = PortfolioExecutionPlan(
        portfolio_name=doc.meta.name,
        semantics_method=portfolio.semantics.method,
        assets=[a.model_dump(exclude_none=True) for a in portfolio.assets],
        scenarios=resolved_scenarios,
        dependency=dependency_plan,
    )

    return PlanReport(ok=True, errors=[], warnings=warnings, plan=plan)


def plan_bundle(bundle: CRPortfolioBundle) -> PlanReport:
    """Resolve an inlined CRPortfolioBundle into an execution-friendly plan.

    Unlike `plan_portfolio`, this function does not access the filesystem.
    It expects scenarios (and optionally control packs) to already be inlined
    inside the bundle.
    """

    errors: list[PlanMessage] = []
    warnings: list[PlanMessage] = []

    payload = bundle.portfolio_bundle
    doc = payload.portfolio
    portfolio: Portfolio = doc.portfolio

    assets_by_name: dict[str, Any] = {a.name: a for a in portfolio.assets}
    all_asset_names = list(assets_by_name.keys())

    # --- Load packs from the bundle (optional) ---
    catalog_ids: set[str] = set()
    assessment_by_id: dict[str, ControlAssessment] = {}

    for cat_doc in payload.control_catalogs or []:
        try:
            for entry in cat_doc.catalog.controls:
                catalog_ids.add(entry.id)
        except Exception as e:
            warnings.append(PlanMessage(level="warning", path="bundle.control_catalogs", message=str(e)))

    for idx, assess_doc in enumerate(payload.control_assessments or []):
        try:
            for a in assess_doc.assessment.assessments:
                if a.id in assessment_by_id:
                    warnings.append(
                        PlanMessage(
                            level="warning",
                            path=f"bundle.control_assessments[{idx}]",
                            message=f"Duplicate assessment for control id '{a.id}' across packs; last one wins.",
                        )
                    )
                assessment_by_id[a.id] = a
        except Exception as e:
            warnings.append(PlanMessage(level="warning", path=f"bundle.control_assessments[{idx}]", message=str(e)))

    # --- Build portfolio inventory (highest precedence) ---
    portfolio_controls_by_id: dict[str, Any] = {}
    for idx, c in enumerate(portfolio.controls or []):
        portfolio_controls_by_id[c.id] = c
        if catalog_ids and c.id not in catalog_ids:
            errors.append(
                PlanMessage(
                    level="error",
                    path=f"portfolio.controls[{idx}].id",
                    message=f"Unknown control id '{c.id}' (not present in referenced catalog pack(s)).",
                )
            )

    # --- Dependency normalization (optional) ---
    dependency_plan: Optional[dict[str, Any]] = None
    if portfolio.dependency is not None and portfolio.dependency.copula is not None:
        cop = portfolio.dependency.copula
        targets = list(cop.targets or [])
        dim = len(targets)
        bad_targets = [t for t in targets if not _is_control_state_ref(t)]
        if bad_targets:
            errors.append(
                PlanMessage(
                    level="error",
                    path="portfolio.dependency.copula.targets",
                    message=f"Unsupported target reference(s): {bad_targets}. Supported: control:<id>:state",
                )
            )
        else:
            target_control_ids = [_extract_control_id_from_state_ref(t) for t in targets]
            for t in target_control_ids:
                if t not in portfolio_controls_by_id and t not in assessment_by_id:
                    errors.append(
                        PlanMessage(
                            level="error",
                            path="portfolio.dependency.copula.targets",
                            message=f"Copula target control id '{t}' not found in portfolio.controls or control assessments.",
                        )
                    )

            corr: Optional[list[list[float]]] = None
            if cop.matrix is not None:
                corr = [list(row) for row in cop.matrix]
            else:
                rho = cop.rho
                if cop.structure not in (None, "toeplitz"):
                    errors.append(
                        PlanMessage(
                            level="error",
                            path="portfolio.dependency.copula.structure",
                            message=f"Unsupported copula structure '{cop.structure}'.",
                        )
                    )
                if rho is None:
                    errors.append(
                        PlanMessage(
                            level="error",
                            path="portfolio.dependency.copula.rho",
                            message="Toeplitz copula requires 'rho' when 'matrix' is not provided.",
                        )
                    )
                else:
                    corr = _toeplitz_corr(dim=dim, rho=float(rho))

            if corr is not None:
                err = _validate_corr_matrix(corr, dim=dim)
                if err:
                    errors.append(PlanMessage(level="error", path="portfolio.dependency.copula", message=err))
                else:
                    dependency_plan = {
                        "copula": {
                            "type": cop.type,
                            "targets": targets,
                            "matrix": corr,
                        }
                    }

    # Scenario lookup by id
    scenario_by_id: dict[str, CRScenarioSchema] = {s.id: s.scenario for s in (bundle.scenarios or [])}

    resolved_scenarios: list[ResolvedScenario] = []
    for idx, sref in enumerate(portfolio.scenarios):
        assert isinstance(sref, ScenarioRef)

        scenario_doc = scenario_by_id.get(sref.id)
        if scenario_doc is None:
            errors.append(
                PlanMessage(
                    level="error",
                    path=f"portfolio.scenarios[{idx}].id",
                    message=f"Bundle is missing inlined scenario for id '{sref.id}'.",
                )
            )
            continue

        # Binding resolution
        applies_to_assets = sref.binding.applies_to_assets
        if applies_to_assets is None:
            applies_to_assets_list = list(all_asset_names)
        else:
            applies_to_assets_list = list(applies_to_assets)

        basis = scenario_doc.scenario.frequency.basis
        if basis == "per_organization_per_year" and applies_to_assets is not None:
            warnings.append(
                PlanMessage(
                    level="warning",
                    path=f"portfolio.scenarios[{idx}].binding.applies_to_assets",
                    message=(
                        "Scenario frequency basis is 'per_organization_per_year'; asset binding does not affect cardinality (cardinality stays 1). "
                        "If you intended per-asset scaling, consider 'per_asset_unit_per_year'."
                    ),
                )
            )

        unknown_assets = [a for a in applies_to_assets_list if a not in assets_by_name]
        if unknown_assets:
            errors.append(
                PlanMessage(
                    level="error",
                    path=f"portfolio.scenarios[{idx}].binding.applies_to_assets",
                    message=f"Unknown asset(s) referenced: {unknown_assets}",
                )
            )
            continue

        if basis == "per_asset_unit_per_year":
            if not applies_to_assets_list:
                errors.append(
                    PlanMessage(
                        level="error",
                        path=f"portfolio.scenarios[{idx}].binding.applies_to_assets",
                        message="Scenario uses per_asset_unit_per_year but no assets are bound (empty applies_to_assets).",
                    )
                )
                continue
            cardinality = int(sum(int(assets_by_name[a].cardinality) for a in applies_to_assets_list))
        else:
            cardinality = 1

        # Controls
        controls_any = scenario_doc.scenario.controls or []
        controls_norm = _scenario_controls_to_objects(list(controls_any))
        resolved_controls: list[ResolvedScenarioControl] = []

        for (cid, scenario_eff_factor, scenario_cov_factor, scenario_potency_factor) in controls_norm:
            inventory_eff: Optional[float] = None
            inventory_cov_val: Optional[float] = None
            inventory_cov_basis: Optional[str] = None
            inventory_rel: Optional[float] = None
            affects: Optional[str] = None

            inv = portfolio_controls_by_id.get(cid)
            if inv is not None:
                if inv.implementation_effectiveness is not None:
                    inventory_eff = float(inv.implementation_effectiveness)
                if inv.coverage is not None:
                    inventory_cov_val = float(inv.coverage.value)
                    inventory_cov_basis = str(inv.coverage.basis)
                if getattr(inv, "reliability", None) is not None:
                    inventory_rel = float(inv.reliability)
                if getattr(inv, "affects", None) is not None:
                    affects = str(inv.affects)
            else:
                assess = assessment_by_id.get(cid)
                if assess is not None:
                    if assess.implementation_effectiveness is not None:
                        inventory_eff = float(assess.implementation_effectiveness)
                    if assess.coverage is not None:
                        inventory_cov_val = float(assess.coverage.value)
                        inventory_cov_basis = str(assess.coverage.basis)
                    if getattr(assess, "reliability", None) is not None:
                        inventory_rel = float(assess.reliability)
                    if getattr(assess, "affects", None) is not None:
                        affects = str(assess.affects)

            if inventory_eff is None and inventory_cov_val is None:
                errors.append(
                    PlanMessage(
                        level="error",
                        path=f"portfolio.scenarios[{idx}].id",
                        message=f"Scenario references control id '{cid}' but no inventory/assessment data is available for it.",
                    )
                )
                continue

            eff_factor = float(scenario_eff_factor) if scenario_eff_factor is not None else None
            pot_factor = float(scenario_potency_factor) if scenario_potency_factor is not None else None
            cov_factor_val: Optional[float] = None
            cov_factor_basis: Optional[str] = None
            if scenario_cov_factor is not None:
                cov_factor_val = float(scenario_cov_factor[0])
                cov_factor_basis = str(scenario_cov_factor[1])

            combined_eff = None
            if inventory_eff is not None:
                combined_eff = _clamp01(
                    inventory_eff
                    * (eff_factor if eff_factor is not None else 1.0)
                    * (pot_factor if pot_factor is not None else 1.0)
                )

            combined_cov = None
            if inventory_cov_val is not None:
                combined_cov = _clamp01(inventory_cov_val * (cov_factor_val if cov_factor_val is not None else 1.0))

            combined_rel = _clamp01(inventory_rel if inventory_rel is not None else 1.0)

            resolved_controls.append(
                ResolvedScenarioControl(
                    id=cid,
                    inventory_implementation_effectiveness=inventory_eff,
                    inventory_coverage_value=inventory_cov_val,
                    inventory_coverage_basis=inventory_cov_basis,
                    inventory_reliability=inventory_rel,
                    affects=affects,
                    scenario_implementation_effectiveness_factor=eff_factor,
                    scenario_coverage_factor=cov_factor_val,
                    scenario_coverage_basis=cov_factor_basis,
                    scenario_potency_factor=pot_factor,
                    combined_implementation_effectiveness=combined_eff,
                    combined_coverage_value=combined_cov,
                    combined_reliability=combined_rel,
                )
            )

            if inventory_cov_basis and cov_factor_basis and inventory_cov_basis != cov_factor_basis:
                warnings.append(
                    PlanMessage(
                        level="warning",
                        path=f"portfolio.scenarios[{idx}].id",
                        message=(
                            f"Control '{cid}' combines coverage with different bases: inventory='{inventory_cov_basis}', scenario='{cov_factor_basis}'. "
                            "Treating scenario coverage as a pure factor."
                        ),
                    )
                )

        resolved_scenarios.append(
            ResolvedScenario(
                id=sref.id,
                path=sref.path,
                resolved_path=None,
                weight=sref.weight,
                applies_to_assets=applies_to_assets_list,
                cardinality=cardinality,
                scenario_name=scenario_doc.meta.name,
                controls=resolved_controls,
            )
        )

    if errors:
        return PlanReport(ok=False, errors=errors, warnings=warnings, plan=None)

    plan = PortfolioExecutionPlan(
        portfolio_name=doc.meta.name,
        semantics_method=portfolio.semantics.method,
        assets=[a.model_dump(exclude_none=True) for a in portfolio.assets],
        scenarios=resolved_scenarios,
        dependency=dependency_plan,
    )

    return PlanReport(ok=True, errors=[], warnings=warnings, plan=plan)
