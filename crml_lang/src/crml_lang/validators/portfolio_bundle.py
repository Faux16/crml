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


def _as_dict(value: Any) -> Optional[dict[str, Any]]:
    return value if isinstance(value, dict) else None


def _as_list(value: Any) -> Optional[list[Any]]:
    return value if isinstance(value, list) else None


def _get_dict(d: dict[str, Any], key: str) -> Optional[dict[str, Any]]:
    return _as_dict(d.get(key))


def _iter_list_dicts(value: Any) -> Iterator[dict[str, Any]]:
    items = _as_list(value)
    if not items:
        return
    for item in items:
        d = _as_dict(item)
        if d is not None:
            yield d


def _iter_pack_docs(pb: dict[str, Any], pack_field: str) -> Iterator[dict[str, Any]]:
    """Iterate over a bundle pack field that is a list of documents."""
    yield from _iter_list_dicts(pb.get(pack_field))


def _iter_inlined_scenario_payloads(pb: dict[str, Any]) -> Iterator[dict[str, Any]]:
    for entry in _iter_pack_docs(pb, "scenarios"):
        sc_doc = _get_dict(entry, "scenario")
        if sc_doc is None:
            continue
        sc_payload = _get_dict(sc_doc, "scenario")
        if sc_payload is None:
            continue
        yield sc_payload


def _bundle_has_scenario_controls(pb: dict[str, Any]) -> bool:
    for sc_payload in _iter_inlined_scenario_payloads(pb):
        if _is_nonempty_list(sc_payload.get("controls")):
            return True
    return False


def _bundle_has_inventory_controls(pb: dict[str, Any]) -> bool:
    portfolio_payload = _portfolio_payload_from_bundle(pb)
    if portfolio_payload is None:
        return False
    return _is_nonempty_list(portfolio_payload.get("controls"))


def _bundle_has_assessments(pb: dict[str, Any]) -> bool:
    return _is_nonempty_list(pb.get("assessments"))


def _bundle_has_control_relationships(pb: dict[str, Any]) -> bool:
    return _is_nonempty_list(pb.get("control_relationships"))


def _bundle_has_attack_control_relationships(pb: dict[str, Any]) -> bool:
    return _is_nonempty_list(pb.get("attack_control_relationships"))


def _iter_scenario_control_ids(pb: dict[str, Any]) -> Iterator[str]:
    """Yield control ids referenced by inlined scenarios (best-effort)."""
    for sc_payload in _iter_inlined_scenario_payloads(pb):
        controls = _as_list(sc_payload.get("controls"))
        if not controls:
            continue
        for c in controls:
            if isinstance(c, str):
                yield c
                continue
            d = _as_dict(c)
            if d is None:
                continue
            cid = d.get("id")
            if isinstance(cid, str):
                yield cid


def _portfolio_payload_from_bundle(pb: dict[str, Any]) -> Optional[dict[str, Any]]:
    portfolio_doc = _as_dict(pb.get("portfolio"))
    if portfolio_doc is None:
        return None
    return _as_dict(portfolio_doc.get("portfolio"))


def _iter_portfolio_inventory_control_ids(pb: dict[str, Any]) -> Iterator[str]:
    portfolio_payload = _portfolio_payload_from_bundle(pb)
    if portfolio_payload is None:
        return
    controls = _as_list(portfolio_payload.get("controls"))
    if not controls:
        return
    for c in controls:
        d = _as_dict(c)
        if d is None:
            continue
        cid = d.get("id")
        if isinstance(cid, str):
            yield cid


def _iter_assessment_control_ids(pb: dict[str, Any]) -> Iterator[str]:
    for doc in _iter_pack_docs(pb, "assessments"):
        payload = _get_dict(doc, "assessment")
        if payload is None:
            continue
        for e in _iter_list_dicts(payload.get("assessments")):
            cid = e.get("id")
            if isinstance(cid, str):
                yield cid


def _iter_control_catalog_control_ids(pb: dict[str, Any]) -> Iterator[str]:
    for doc in _iter_pack_docs(pb, "control_catalogs"):
        payload = _get_dict(doc, "catalog")
        if payload is None:
            continue
        for c in _iter_list_dicts(payload.get("controls")):
            cid = c.get("id")
            if isinstance(cid, str):
                yield cid


def _iter_control_relationship_doc_edges(doc: dict[str, Any]) -> Iterator[tuple[str, str]]:
    payload = _get_dict(doc, "relationships")
    if payload is None:
        return
    rels = _as_list(payload.get("relationships"))
    if not rels:
        return

    for r in rels:
        rd = _as_dict(r)
        if rd is None:
            continue
        source = rd.get("source")
        if not isinstance(source, str):
            continue
        for t in _iter_list_dicts(rd.get("targets")):
            target = t.get("target")
            if isinstance(target, str):
                yield source, target


def _iter_control_relationship_edges(pb: dict[str, Any]) -> Iterator[tuple[str, str]]:
    """Yield (source, target) control ids for all control_relationships packs."""
    for doc in _iter_pack_docs(pb, "control_relationships"):
        yield from _iter_control_relationship_doc_edges(doc)


def _iter_attack_control_doc_targets(doc: dict[str, Any]) -> Iterator[str]:
    payload = _get_dict(doc, "relationships")
    if payload is None:
        return
    for r in _iter_list_dicts(payload.get("relationships")):
        for t in _iter_list_dicts(r.get("targets")):
            cid = t.get("control")
            if isinstance(cid, str):
                yield cid


def _iter_attack_control_relationship_targets(pb: dict[str, Any]) -> Iterator[str]:
    for doc in _iter_pack_docs(pb, "attack_control_relationships"):
        yield from _iter_attack_control_doc_targets(doc)


def _errors_for_missing_inlined_packs(pb: dict[str, Any]) -> list[ValidationMessage]:
    errors: list[ValidationMessage] = []
    portfolio_payload = _portfolio_payload_from_bundle(pb) or {}

    referenced_pack_fields: list[tuple[str, str]] = [
        ("assessments", "portfolio.assessments"),
        ("control_catalogs", "portfolio.control_catalogs"),
        ("control_relationships", "portfolio.control_relationships"),
        ("attack_catalogs", "portfolio.attack_catalogs"),
        ("attack_control_relationships", "portfolio.attack_control_relationships"),
    ]

    for bundle_field, portfolio_field in referenced_pack_fields:
        refs = portfolio_payload.get(bundle_field)
        if _is_nonempty_list(refs) and not _is_nonempty_list(pb.get(bundle_field)):
            errors.append(
                ValidationMessage(
                    level="error",
                    source="semantic",
                    path=f"portfolio_bundle.{bundle_field}",
                    message=(
                        f"Portfolio references '{portfolio_field}' but the bundle does not inline any '{bundle_field}' documents. "
                        "A portfolio bundle is expected to be self-contained; inline the referenced documents or remove the references."
                    ),
                )
            )

    return errors


def _errors_for_missing_inlined_scenarios(pb: dict[str, Any]) -> list[ValidationMessage]:
    errors: list[ValidationMessage] = []
    portfolio_payload = _portfolio_payload_from_bundle(pb) or {}

    portfolio_scenarios = _as_list(portfolio_payload.get("scenarios"))
    if not portfolio_scenarios:
        return errors

    expected_ids: list[str] = []
    for s in portfolio_scenarios:
        sd = _as_dict(s)
        if sd is not None and isinstance(sd.get("id"), str):
            expected_ids.append(sd["id"])

    inlined_ids: set[str] = set()
    for s in _iter_pack_docs(pb, "scenarios"):
        sid = s.get("id")
        if isinstance(sid, str):
            inlined_ids.add(sid)

    for idx, sid in enumerate(expected_ids):
        if sid not in inlined_ids:
            errors.append(
                ValidationMessage(
                    level="error",
                    source="semantic",
                    path=f"portfolio_bundle.portfolio.portfolio.scenarios[{idx}].id",
                    message=f"Bundle is missing an inlined scenario for portfolio scenario id '{sid}'.",
                )
            )

    return errors


def _errors_for_controls_and_mappings(pb: dict[str, Any]) -> list[ValidationMessage]:
    errors: list[ValidationMessage] = []

    scenario_control_ids = set(_iter_scenario_control_ids(pb))
    if not scenario_control_ids:
        return errors

    inventory_ids = set(_iter_portfolio_inventory_control_ids(pb))
    assessment_ids = set(_iter_assessment_control_ids(pb))
    posture_ids = inventory_ids | assessment_ids

    if not posture_ids:
        errors.append(
            ValidationMessage(
                level="error",
                source="semantic",
                path="portfolio_bundle",
                message=(
                    "One or more inlined scenarios reference controls, but the bundle provides no control posture "
                    "(neither portfolio.controls inventory nor inlined assessments). Include assessments and/or portfolio controls."
                ),
            )
        )
        return errors

    missing_mapping_targets: set[str] = set()
    source_has_applicable_target: set[str] = set()
    for source, target in _iter_control_relationship_edges(pb):
        if target not in posture_ids:
            missing_mapping_targets.add(target)
        else:
            source_has_applicable_target.add(source)

    if missing_mapping_targets:
        errors.append(
            ValidationMessage(
                level="error",
                source="semantic",
                path="portfolio_bundle.control_relationships",
                message=(
                    "Bundle includes control_relationships that map to target control id(s) not present in portfolio.controls or assessments: "
                    f"{sorted(missing_mapping_targets)}. "
                    "Mappings should target implemented/assessed controls so engines/tools can resolve them."
                ),
            )
        )

    missing_attack_targets = sorted(
        {t for t in _iter_attack_control_relationship_targets(pb) if t not in posture_ids}
    )
    if missing_attack_targets:
        errors.append(
            ValidationMessage(
                level="error",
                source="semantic",
                path="portfolio_bundle.attack_control_relationships",
                message=(
                    "Bundle includes attack_control_relationships that reference control id(s) not present in portfolio.controls or assessments: "
                    f"{missing_attack_targets}. "
                    "Mappings should point at implemented/assessed controls to be actionable."
                ),
            )
        )

    unresolved = sorted(
        [
            cid
            for cid in scenario_control_ids
            if cid not in posture_ids and cid not in source_has_applicable_target
        ]
    )
    if unresolved:
        errors.append(
            ValidationMessage(
                level="error",
                source="semantic",
                path="portfolio_bundle.scenarios",
                message=(
                    "One or more scenario control ids are not resolvable from bundle control posture and mappings. "
                    "Each scenario control must either exist in portfolio.controls/assessments, or have a control_relationships mapping to an implemented/assessed target. "
                    f"Unresolved: {unresolved}."
                ),
            )
        )

    return errors


def _bundle_semantic_errors(pb: dict[str, Any]) -> list[ValidationMessage]:
    """Semantic errors for bundles that are schema-valid but incomplete/inconsistent."""
    errors: list[ValidationMessage] = []
    errors.extend(_errors_for_missing_inlined_packs(pb))
    errors.extend(_errors_for_missing_inlined_scenarios(pb))
    errors.extend(_errors_for_controls_and_mappings(pb))
    return errors


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

    if errors:
        return ValidationReport(ok=False, errors=errors, warnings=[])

    pb = data.get("portfolio_bundle")
    semantic_errors: list[ValidationMessage] = []
    if isinstance(pb, dict):
        try:
            semantic_errors = _bundle_semantic_errors(pb)
        except Exception:
            # Semantic checks are best-effort; if they crash, don't block schema validation.
            semantic_errors = []

    warnings = _semantic_warnings(data)

    errors.extend(semantic_errors)

    if strict_model and not errors:
        errors.extend(_pydantic_strict_model_errors(data))

    return ValidationReport(ok=(len(errors) == 0), errors=errors, warnings=warnings)
