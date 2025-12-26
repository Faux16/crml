from __future__ import annotations

from typing import Any

from crml_lang.api import CRAssessment, CRControlCatalog

from .config import OscalEndpoint, load_endpoints
from .convert import (
    infer_namespace_and_framework,
    is_valid_namespace,
    slug_namespace,
    oscal_catalog_to_crml_assessment,
    oscal_catalog_to_crml_control_catalog,
)
from .errors import OscalEndpointNotFoundError
from .io import load_oscal_document
from .provenance import OscalProvenance


def get_endpoint(endpoint_id: str) -> OscalEndpoint:
    endpoints = load_endpoints()
    for e in endpoints:
        if e.catalog_id == endpoint_id:
            return e
    raise OscalEndpointNotFoundError(endpoint_id)


def list_endpoints() -> list[dict[str, Any]]:
    """Return endpoints as JSON/YAML-friendly dicts (for UIs/CLIs)."""
    out: list[dict[str, Any]] = []
    for e in load_endpoints():
        out.append(
            {
                "catalog_id": e.catalog_id,
                "description": e.description,
                "url": e.url,
                "path": e.path,
                "source": e.source,
                "kind": e.kind,
                "regions": e.regions,
                "countries": e.countries,
                "locale": e.locale.model_dump(exclude_none=True) if e.locale is not None else None,
                "industries": e.industries,
                "meta": dict(e.meta_overrides) if e.meta_overrides is not None else None,
                "framework": e.framework_override,
                "namespace": e.namespace_override,
                "meta_name": e.meta_name,
                "mapping_type": e.mapping_type,
                "portfolio_meta_name": e.portfolio_meta_name,
                "default_cardinality": e.default_cardinality,
                "timeout_seconds": e.timeout_seconds,
            }
        )
    return out


def _effective_namespace(*, inferred: str, endpoint: OscalEndpoint) -> str:
    if endpoint.namespace_override:
        return endpoint.namespace_override

    # Prefer catalog_id as a stable namespace if provided.
    # This makes control ids stable even if upstream OSCAL metadata.title changes.
    return (
        endpoint.catalog_id
        if is_valid_namespace(endpoint.catalog_id)
        else slug_namespace(endpoint.catalog_id)
    )


def load_oscal_from_endpoint(
    endpoint_id: str,
    *,
    user_agent: Optional[str] = None,
) -> tuple[OscalEndpoint, dict[str, Any], OscalProvenance]:
    endpoint = get_endpoint(endpoint_id)
    doc, prov = load_oscal_from_endpoint_obj(endpoint, endpoint_id=endpoint_id, user_agent=user_agent)
    return endpoint, doc, prov


def load_oscal_from_endpoint_obj(
    endpoint: OscalEndpoint,
    *,
    endpoint_id: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> tuple[dict[str, Any], OscalProvenance]:
    doc = load_oscal_document(
        url=endpoint.url,
        path=endpoint.path,
        timeout_seconds=endpoint.timeout_seconds,
        user_agent=user_agent,
        source_label=f"endpoint:{endpoint_id or endpoint.catalog_id}",
    )

    prov = OscalProvenance(
        source_kind="endpoint",
        source=endpoint.source,
        endpoint_id=endpoint_id or endpoint.catalog_id,
        fetched_at_utc=OscalProvenance.now_utc_iso(),
    )
    return doc, prov


def control_catalog_from_endpoint(
    endpoint_id: str,
    *,
    user_agent: Optional[str] = None,
) -> tuple[CRControlCatalog, OscalProvenance]:
    endpoint = get_endpoint(endpoint_id)
    return control_catalog_from_endpoint_obj(endpoint, endpoint_id=endpoint_id, user_agent=user_agent)


def control_catalog_from_endpoint_obj(
    endpoint: OscalEndpoint,
    *,
    endpoint_id: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> tuple[CRControlCatalog, OscalProvenance]:
    doc, prov = load_oscal_from_endpoint_obj(endpoint, endpoint_id=endpoint_id, user_agent=user_agent)

    namespace, framework = infer_namespace_and_framework(doc)
    namespace = _effective_namespace(inferred=namespace, endpoint=endpoint)

    from .standards import detect_standard_id, get_control_text_options

    standard_id = detect_standard_id(
        endpoint_id=endpoint_id or endpoint.catalog_id,
        catalog_id=endpoint.catalog_id,
    )
    control_text_options = get_control_text_options(standard_id)

    payload = oscal_catalog_to_crml_control_catalog(
        doc,
        namespace=namespace,
        framework=framework,
        catalog_id=endpoint.catalog_id,
        meta_name=endpoint.meta_name or None,
        source_url=endpoint.url,
        control_text_options=control_text_options,
    )

    meta = payload.get("meta")
    if isinstance(meta, dict):
        if endpoint.meta_overrides is not None:
            meta.update(endpoint.meta_overrides)
        else:
            # Backwards-compatible injection path.
            if endpoint.locale is not None:
                meta["locale"] = endpoint.locale.model_dump(exclude_none=True)
            if endpoint.industries is not None:
                meta["industries"] = endpoint.industries
    return CRControlCatalog.model_validate(payload), prov


def assessment_template_from_endpoint(
    endpoint_id: str,
    *,
    user_agent: Optional[str] = None,
) -> tuple[CRAssessment, OscalProvenance]:
    endpoint, doc, prov = load_oscal_from_endpoint(
        endpoint_id,
        user_agent=user_agent,
    )

    namespace, framework = infer_namespace_and_framework(doc)
    namespace = _effective_namespace(inferred=namespace, endpoint=endpoint)

    payload = oscal_catalog_to_crml_assessment(
        doc,
        namespace=namespace,
        framework=framework,
        assessment_id=None,
        meta_name=None,
        source_url=endpoint.url,
        default_scf_cmm_level=0,
    )
    return CRAssessment.model_validate(payload), prov
