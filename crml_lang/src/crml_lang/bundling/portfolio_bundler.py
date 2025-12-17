from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Literal, Mapping, Optional

from crml_lang.models.control_assessment_model import CRControlAssessmentSchema
from crml_lang.models.control_catalog_model import CRControlCatalogSchema
from crml_lang.models.control_relationships_model import CRControlRelationshipsSchema
from crml_lang.models.crml_model import CRScenarioSchema
from crml_lang.models.portfolio_bundle import (
    BundleMessage,
    BundledScenario,
    CRPortfolioBundle,
    PortfolioBundlePayload,
)
from crml_lang.models.portfolio_model import CRPortfolioSchema


@dataclass(frozen=True)
class BundleReport:
    """Structured bundle output (errors/warnings + bundle when successful)."""

    ok: bool
    errors: list[BundleMessage]
    warnings: list[BundleMessage]
    bundle: Optional[CRPortfolioBundle] = None


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


def _load_portfolio_doc(
    source: str | dict[str, Any] | CRPortfolioSchema,
    *,
    source_kind: Literal["path", "yaml", "data", "model"],
) -> tuple[CRPortfolioSchema | None, dict[str, Any] | None, str | None, list[BundleMessage]]:
    """Load/validate the portfolio document and determine base_dir for resolving references."""

    errors: list[BundleMessage] = []
    base_dir: str | None = None

    if source_kind == "model":
        if not isinstance(source, CRPortfolioSchema):
            errors.append(
                BundleMessage(
                    level="error",
                    path="(input)",
                    message="source_kind='model' requires a CRPortfolio/CRPortfolioSchema instance",
                )
            )
            return None, None, None, errors
        return source, None, None, errors

    data: dict[str, Any]
    if source_kind == "path":
        assert isinstance(source, str)
        base_dir = os.path.dirname(os.path.abspath(source))
        try:
            data = _load_yaml_file(source)
        except Exception as e:
            errors.append(BundleMessage(level="error", path="(io)", message=str(e)))
            return None, None, base_dir, errors
    elif source_kind == "yaml":
        assert isinstance(source, str)
        try:
            import yaml
        except Exception as e:
            errors.append(BundleMessage(level="error", path="(io)", message=f"PyYAML is required: {e}"))
            return None, None, None, errors

        loaded = yaml.safe_load(source)
        if not isinstance(loaded, dict):
            errors.append(BundleMessage(level="error", path="(root)", message="YAML must be a mapping"))
            return None, None, None, errors
        data = loaded
    else:
        assert isinstance(source, dict)
        data = source

    try:
        portfolio_doc = CRPortfolioSchema.model_validate(data)
    except Exception as e:
        errors.append(BundleMessage(level="error", path="(schema)", message=str(e)))
        return None, data, base_dir, errors

    return portfolio_doc, data, base_dir, errors


def _inline_pack_paths(
    *,
    paths: list[str],
    base_dir: str | None,
    source_kind: Literal["path", "yaml", "data", "model"],
    warnings: list[BundleMessage],
    model_mode_warning_path_prefix: str,
    model_mode_warning_message: str,
) -> list[str]:
    if source_kind == "model":
        for idx, _ in enumerate(paths):
            warnings.append(
                BundleMessage(
                    level="warning",
                    path=f"{model_mode_warning_path_prefix}[{idx}]",
                    message=model_mode_warning_message,
                )
            )
        return []

    resolved_paths: list[str] = []
    for p in paths:
        if not isinstance(p, str) or not p:
            continue
        resolved_paths.append(_resolve_path(base_dir, p))
    return resolved_paths


def _inline_control_catalogs(
    *,
    portfolio_doc: CRPortfolioSchema,
    base_dir: str | None,
    source_kind: Literal["path", "yaml", "data", "model"],
    warnings: list[BundleMessage],
    initial: list[CRControlCatalogSchema],
) -> list[CRControlCatalogSchema]:
    out = list(initial)
    paths = portfolio_doc.portfolio.control_catalogs or []

    resolved_paths = _inline_pack_paths(
        paths=list(paths),
        base_dir=base_dir,
        source_kind=source_kind,
        warnings=warnings,
        model_mode_warning_path_prefix="portfolio.control_catalogs",
        model_mode_warning_message=(
            "Portfolio references a control catalog path, but bundling is in model-mode; "
            "provide `control_catalogs` to inline cataloge content."
        ),
    )

    for idx, rp in enumerate(resolved_paths):
        original = paths[idx]
        try:
            out.append(CRControlCatalogSchema.model_validate(_load_yaml_file(rp)))
        except Exception as e:
            warnings.append(
                BundleMessage(
                    level="warning",
                    path=f"portfolio.control_catalogs[{idx}]",
                    message=f"Failed to inline control catalog '{original}': {e}",
                )
            )

    return out


def _inline_control_assessments(
    *,
    portfolio_doc: CRPortfolioSchema,
    base_dir: str | None,
    source_kind: Literal["path", "yaml", "data", "model"],
    warnings: list[BundleMessage],
    initial: list[CRControlAssessmentSchema],
) -> list[CRControlAssessmentSchema]:
    out = list(initial)
    paths = portfolio_doc.portfolio.control_assessments or []

    resolved_paths = _inline_pack_paths(
        paths=list(paths),
        base_dir=base_dir,
        source_kind=source_kind,
        warnings=warnings,
        model_mode_warning_path_prefix="portfolio.control_assessments",
        model_mode_warning_message=(
            "Portfolio references a control assessment path, but bundling is in model-mode; "
            "provide `control_assessments` to inline cataloge content."
        ),
    )

    for idx, rp in enumerate(resolved_paths):
        original = paths[idx]
        try:
            out.append(CRControlAssessmentSchema.model_validate(_load_yaml_file(rp)))
        except Exception as e:
            warnings.append(
                BundleMessage(
                    level="warning",
                    path=f"portfolio.control_assessments[{idx}]",
                    message=f"Failed to inline control assessment '{original}': {e}",
                )
            )

    return out


def _inline_control_relationships(
    *,
    portfolio_doc: CRPortfolioSchema,
    base_dir: str | None,
    source_kind: Literal["path", "yaml", "data", "model"],
    warnings: list[BundleMessage],
    initial: list[CRControlRelationshipsSchema],
) -> list[CRControlRelationshipsSchema]:
    out = list(initial)
    paths = portfolio_doc.portfolio.control_relationships or []

    resolved_paths = _inline_pack_paths(
        paths=list(paths),
        base_dir=base_dir,
        source_kind=source_kind,
        warnings=warnings,
        model_mode_warning_path_prefix="portfolio.control_relationships",
        model_mode_warning_message=(
            "Portfolio references a control relationships path, but bundling is in model-mode; "
            "provide `control_relationships` to inline pack content."
        ),
    )

    for idx, rp in enumerate(resolved_paths):
        original = paths[idx]
        try:
            out.append(CRControlRelationshipsSchema.model_validate(_load_yaml_file(rp)))
        except Exception as e:
            warnings.append(
                BundleMessage(
                    level="warning",
                    path=f"portfolio.control_relationships[{idx}]",
                    message=f"Failed to inline control relationships pack '{original}': {e}",
                )
            )

    return out


def _inline_scenarios(
    *,
    portfolio_doc: CRPortfolioSchema,
    base_dir: str | None,
    source_kind: Literal["path", "yaml", "data", "model"],
    scenarios: Mapping[str, CRScenarioSchema] | None,
) -> tuple[list[BundledScenario], list[BundleMessage]]:
    errors: list[BundleMessage] = []
    bundled: list[BundledScenario] = []

    for idx, sref in enumerate(portfolio_doc.portfolio.scenarios):
        if source_kind == "model":
            if not scenarios:
                errors.append(
                    BundleMessage(
                        level="error",
                        path="(input)",
                        message="source_kind='model' requires `scenarios` to be provided",
                    )
                )
                return [], errors

            scenario_doc = scenarios.get(sref.id) or scenarios.get(sref.path)
            if scenario_doc is None:
                errors.append(
                    BundleMessage(
                        level="error",
                        path=f"portfolio.scenarios[{idx}]",
                        message=(
                            f"Missing inlined scenario for reference id='{sref.id}', path='{sref.path}'. "
                            "Provide it via the `scenarios` mapping (key by id or path)."
                        ),
                    )
                )
                return [], errors
        else:
            scenario_path = _resolve_path(base_dir, sref.path)
            try:
                scenario_doc = CRScenarioSchema.model_validate(_load_yaml_file(scenario_path))
            except Exception as e:
                errors.append(
                    BundleMessage(
                        level="error",
                        path=f"portfolio.scenarios[{idx}].path",
                        message=f"Failed to inline scenario '{sref.id}' from '{sref.path}': {e}",
                    )
                )
                return [], errors

        bundled.append(
            BundledScenario(
                id=sref.id,
                weight=sref.weight,
                source_path=sref.path,
                scenario=scenario_doc,
            )
        )

    return bundled, errors


def bundle_portfolio(
    source: str | dict[str, Any] | CRPortfolioSchema,
    *,
    source_kind: Literal["path", "yaml", "data", "model"] = "path",
    scenarios: Mapping[str, CRScenarioSchema] | None = None,
    control_catalogs: list[CRControlCatalogSchema] | None = None,
    control_assessments: list[CRControlAssessmentSchema] | None = None,
    control_relationships: list[CRControlRelationshipsSchema] | None = None,
) -> BundleReport:
    """Build an engine-agnostic CRPortfolioBundle from a portfolio input.

    Bundling is intentionally *not* planning:
    - it inlines referenced documents (scenarios and optionally control packs)
    - it does not compute planning-derived fields (e.g., cardinality, resolved control effects)

        Engines should be able to run a bundle without filesystem access.

        Notes
        -----
        - The first argument (`source`) is the *portfolio input*.
        - When `source_kind="path"|"yaml"|"data"`, referenced scenarios/packs are loaded from disk.
        - When `source_kind="model"`, you must provide referenced scenario documents via `scenarios`
            (keyed by scenario id or path), and optionally provide `control_catalogs` / `control_assessments`.
    """

    warnings: list[BundleMessage] = []

    portfolio_doc, _, base_dir, load_errors = _load_portfolio_doc(source, source_kind=source_kind)
    if load_errors or portfolio_doc is None:
        return BundleReport(ok=False, errors=load_errors, warnings=warnings, bundle=None)

    control_catalogs_out = _inline_control_catalogs(
        portfolio_doc=portfolio_doc,
        base_dir=base_dir,
        source_kind=source_kind,
        warnings=warnings,
        initial=list(control_catalogs or []),
    )

    control_assessments_out = _inline_control_assessments(
        portfolio_doc=portfolio_doc,
        base_dir=base_dir,
        source_kind=source_kind,
        warnings=warnings,
        initial=list(control_assessments or []),
    )

    control_relationships_out = _inline_control_relationships(
        portfolio_doc=portfolio_doc,
        base_dir=base_dir,
        source_kind=source_kind,
        warnings=warnings,
        initial=list(control_relationships or []),
    )

    # Inline scenarios referenced by the portfolio.
    bundled_scenarios, scenario_errors = _inline_scenarios(
        portfolio_doc=portfolio_doc,
        base_dir=base_dir,
        source_kind=source_kind,
        scenarios=scenarios,
    )
    if scenario_errors:
        return BundleReport(ok=False, errors=scenario_errors, warnings=warnings, bundle=None)

    payload = PortfolioBundlePayload(
        portfolio=portfolio_doc,
        scenarios=bundled_scenarios,
        control_catalogs=control_catalogs_out,
        control_assessments=control_assessments_out,
        control_relationships=control_relationships_out,
        warnings=warnings,
        metadata={
            "source_kind": source_kind,
            **({"source_path": os.path.abspath(source)} if source_kind == "path" and isinstance(source, str) else {}),
        },
    )

    bundle = CRPortfolioBundle(portfolio_bundle=payload)

    return BundleReport(ok=True, errors=[], warnings=warnings, bundle=bundle)
