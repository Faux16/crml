from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any, Literal, Optional, cast

import importlib.resources

from crml_lang.yamlio import load_yaml_mapping_from_str


OscalKind = Literal["catalog", "assets", "mapping"]
OscalMappingType = Literal["control_relationships", "attack_control_relationships"]


@dataclass(frozen=True, slots=True)
class OscalEndpoint:
    id: str
    description: str
    url: str
    kind: OscalKind

    # --- kind: assets ---
    # Creates a CRML portfolio-like asset inventory from an OSCAL source.
    portfolio_meta_name: Optional[str] = None
    default_cardinality: int = 1

    # --- kind: mapping ---
    # Generates a CRML relationships document.
    mapping_type: Optional[OscalMappingType] = None

    # --- common ---
    timeout_seconds: float = 30.0

    # --- kind: catalog (optional overrides) ---
    namespace_override: Optional[str] = None
    framework_override: Optional[str] = None
    catalog_id: Optional[str] = None
    meta_name: Optional[str] = None


def _read_endpoints_yaml_text() -> str:
    return (
        importlib.resources.files(__package__)
        .joinpath("api-endpoints.yaml")
        .read_text(encoding="utf-8")
    )


def _iter_external_endpoint_paths() -> list[str]:
    paths: list[str] = []

    env = os.environ.get("CRML_OSCAL_ENDPOINTS_PATH")
    if env:
        for part in env.split(os.pathsep):
            p = part.strip()
            if p:
                paths.append(p)

    return paths


def _parse_timeout_seconds(endpoint_id: str, timeout_seconds_raw: Any) -> float:
    try:
        timeout_seconds = float(timeout_seconds_raw)
    except Exception as e:
        raise ValueError(
            f"OSCAL endpoint {endpoint_id!r} has invalid timeout_seconds: {timeout_seconds_raw!r}"
        ) from e

    if timeout_seconds <= 0:
        raise ValueError(f"OSCAL endpoint {endpoint_id!r} timeout_seconds must be > 0")

    return timeout_seconds


def _parse_assets_fields(item: dict[str, Any], endpoint_id: str) -> tuple[str, int]:
    portfolio_meta_name = str(item.get("portfolio_meta_name", "")).strip() or None
    if not portfolio_meta_name:
        raise ValueError(f"OSCAL assets endpoint {endpoint_id!r} must set portfolio_meta_name")

    default_cardinality_raw = item.get("default_cardinality", 1)
    try:
        default_cardinality = int(default_cardinality_raw)
    except Exception as e:
        raise ValueError(
            f"OSCAL assets endpoint {endpoint_id!r} has invalid default_cardinality: {default_cardinality_raw!r}"
        ) from e

    if default_cardinality < 1:
        raise ValueError(f"OSCAL assets endpoint {endpoint_id!r} default_cardinality must be >= 1")

    return portfolio_meta_name, default_cardinality


def _parse_mapping_type(item: dict[str, Any], endpoint_id: str) -> OscalMappingType:
    mapping_type_raw = str(item.get("mapping_type", "")).strip() or None
    allowed: tuple[OscalMappingType, ...] = ("control_relationships", "attack_control_relationships")
    if mapping_type_raw not in allowed:
        raise ValueError(
            f"OSCAL mapping endpoint {endpoint_id!r} must set mapping_type to 'control_relationships' or 'attack_control_relationships'"
        )
    return cast(OscalMappingType, mapping_type_raw)


def _parse_endpoint_item(item: Any) -> OscalEndpoint:
    if not isinstance(item, dict):
        raise ValueError("Each OSCAL endpoint must be a mapping")

    endpoint_id = str(item.get("id", "")).strip()
    if not endpoint_id:
        raise ValueError("OSCAL endpoint is missing required field 'id'")

    description = str(item.get("description", "")).strip()
    if not description:
        raise ValueError(f"OSCAL endpoint {endpoint_id!r} is missing required field 'description'")

    url = str(item.get("url", "")).strip()
    if not url:
        raise ValueError(f"OSCAL endpoint {endpoint_id!r} is missing required field 'url'")

    kind_raw = str(item.get("kind", "catalog")).strip() or "catalog"
    if kind_raw not in ("catalog", "assets", "mapping"):
        raise ValueError(f"Unsupported OSCAL endpoint kind: {kind_raw!r}")
    kind = cast(OscalKind, kind_raw)

    timeout_seconds = _parse_timeout_seconds(endpoint_id, item.get("timeout_seconds", 30.0))

    portfolio_meta_name: Optional[str] = None
    default_cardinality = 1
    mapping_type: Optional[OscalMappingType] = None

    namespace_override = str(item.get("namespace", "")).strip() or None
    framework_override = str(item.get("framework", "")).strip() or None
    catalog_id = str(item.get("catalog_id", "")).strip() or None
    meta_name = str(item.get("meta_name", "")).strip() or None

    if kind == "assets":
        portfolio_meta_name, default_cardinality = _parse_assets_fields(item, endpoint_id)
    elif kind == "mapping":
        mapping_type = _parse_mapping_type(item, endpoint_id)

    return OscalEndpoint(
        id=endpoint_id,
        description=description,
        url=url,
        kind=kind,
        portfolio_meta_name=portfolio_meta_name,
        default_cardinality=default_cardinality,
        mapping_type=mapping_type,
        timeout_seconds=timeout_seconds,
        namespace_override=namespace_override,
        framework_override=framework_override,
        catalog_id=catalog_id,
        meta_name=meta_name,
    )


def load_endpoints() -> list[OscalEndpoint]:
    """Load OSCAL endpoints.

    Sources (later sources override earlier by endpoint id):
    - built-in package data file `api-endpoints.yaml`
    - optional external endpoint files provided via `CRML_OSCAL_ENDPOINTS_PATH`
      (pathsep-separated)
    """

    merged: dict[str, OscalEndpoint] = {}

    def merge_text(text: str) -> None:
        raw = load_yaml_mapping_from_str(text)
        endpoints = raw.get("endpoints")
        if endpoints is None:
            return
        if not isinstance(endpoints, list):
            raise ValueError("OSCAL endpoints config must contain a top-level 'endpoints' list")
        for item in endpoints:
            e = _parse_endpoint_item(item)
            merged[e.id] = e

    merge_text(_read_endpoints_yaml_text())

    for p in _iter_external_endpoint_paths():
        merge_text(Path(p).read_text(encoding="utf-8"))

    return list(merged.values())
