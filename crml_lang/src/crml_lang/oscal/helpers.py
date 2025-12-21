from __future__ import annotations

from typing import Any, Optional

from crml_lang.api import CRAssessment, CRControlCatalog

from .config import OscalEndpoint, load_endpoints
from .convert import infer_namespace_and_framework, oscal_catalog_to_crml_assessment, oscal_catalog_to_crml_control_catalog
from .errors import OscalEndpointNotFoundError
from .io import load_oscal_document
from .provenance import OscalProvenance


def get_endpoint(endpoint_id: str, *, extra_paths: Optional[list[str]] = None) -> OscalEndpoint:
    # NOTE: kept for backwards compatibility; load_endpoints() no longer accepts extra_paths.
    del extra_paths
    endpoints = load_endpoints()
    for e in endpoints:
        if e.id == endpoint_id:
            return e
    raise OscalEndpointNotFoundError(endpoint_id)


def list_endpoints(*, extra_paths: Optional[list[str]] = None) -> list[dict[str, Any]]:
    """Return endpoints as JSON/YAML-friendly dicts (for UIs/CLIs)."""

    # NOTE: kept for backwards compatibility; load_endpoints() no longer accepts extra_paths.
    del extra_paths
    out: list[dict[str, Any]] = []
    for e in load_endpoints():
        out.append(
            {
                "id": e.id,
                "description": e.description,
                "url": e.url,
                "kind": e.kind,
                "mapping_type": e.mapping_type,
                "portfolio_meta_name": e.portfolio_meta_name,
                "default_cardinality": e.default_cardinality,
                "timeout_seconds": e.timeout_seconds,
            }
        )
    return out


def load_oscal_from_endpoint(
    endpoint_id: str,
    *,
    extra_paths: Optional[list[str]] = None,
    user_agent: Optional[str] = None,
) -> tuple[OscalEndpoint, dict[str, Any], OscalProvenance]:
    endpoint = get_endpoint(endpoint_id, extra_paths=extra_paths)

    doc = load_oscal_document(
        url=endpoint.url,
        timeout_seconds=endpoint.timeout_seconds,
        user_agent=user_agent,
        source_label=f"endpoint:{endpoint_id}",
    )

    prov = OscalProvenance(
        source_kind="endpoint",
        source=endpoint.url,
        endpoint_id=endpoint_id,
        fetched_at_utc=OscalProvenance.now_utc_iso(),
    )
    return endpoint, doc, prov


def control_catalog_from_endpoint(
    endpoint_id: str,
    *,
    extra_paths: Optional[list[str]] = None,
    user_agent: Optional[str] = None,
) -> tuple[CRControlCatalog, OscalProvenance]:
    endpoint, doc, prov = load_oscal_from_endpoint(
        endpoint_id,
        extra_paths=extra_paths,
        user_agent=user_agent,
    )

    namespace, framework = infer_namespace_and_framework(doc)
    if endpoint.framework_override:
        framework = endpoint.framework_override
    if endpoint.namespace_override:
        namespace = endpoint.namespace_override

    payload = oscal_catalog_to_crml_control_catalog(
        doc,
        namespace=namespace,
        framework=framework,
        catalog_id=endpoint.catalog_id or None,
        meta_name=endpoint.meta_name or None,
        source_url=endpoint.url,
    )
    return CRControlCatalog.model_validate(payload), prov


def assessment_template_from_endpoint(
    endpoint_id: str,
    *,
    extra_paths: Optional[list[str]] = None,
    user_agent: Optional[str] = None,
) -> tuple[CRAssessment, OscalProvenance]:
    endpoint, doc, prov = load_oscal_from_endpoint(
        endpoint_id,
        extra_paths=extra_paths,
        user_agent=user_agent,
    )

    namespace, framework = infer_namespace_and_framework(doc)
    if endpoint.framework_override:
        framework = endpoint.framework_override
    if endpoint.namespace_override:
        namespace = endpoint.namespace_override

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
