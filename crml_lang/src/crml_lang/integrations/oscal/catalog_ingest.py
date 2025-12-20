from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional

from crml_lang import CRControlCatalog
from crml_lang.models.control_catalog_model import ControlCatalog, ControlCatalogEntry
from crml_lang.models.scenario_model import Meta

from ._require import require_oscal


@dataclass(frozen=True)
class OscalCatalogProvenance:
    """Optional provenance metadata recorded into CRML meta.description."""

    source_path: Optional[str] = None
    source_url: Optional[str] = None
    license: Optional[str] = None


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_mapping_from_json_or_yaml(text: str) -> dict[str, Any]:
    # JSON first (fast, strict)
    try:
        import json

        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    # YAML (optional; but crml-lang already depends on pyyaml)
    from crml_lang.yamlio import load_yaml_mapping_from_str

    return load_yaml_mapping_from_str(text)


def read_oscal_catalog(path: str | Path):
    """Read an OSCAL Catalog from JSON or YAML.

    Uses Compliance Trestle when available.

    Returns:
        A `trestle.oscal.catalog.Catalog` instance.
    """

    require_oscal()

    from trestle.oscal.catalog import Catalog  # type: ignore

    p = Path(path)

    # Prefer Trestle's own read path when available.
    if hasattr(Catalog, "oscal_read"):
        return Catalog.oscal_read(str(p))

    # Fallback: parse into dict and construct a model.
    data = _load_mapping_from_json_or_yaml(_read_text(p))

    if hasattr(Catalog, "model_validate"):
        return Catalog.model_validate(data)  # pydantic v2

    if hasattr(Catalog, "parse_obj"):
        return Catalog.parse_obj(data)  # pydantic v1

    raise RuntimeError("Unsupported Trestle Catalog model API")


def _iter_controls_from_group(group: Any) -> Iterable[Any]:
    controls = getattr(group, "controls", None) or []
    for c in controls:
        yield c

    subgroups = getattr(group, "groups", None) or []
    for sg in subgroups:
        yield from _iter_controls_from_group(sg)


def _iter_controls(catalog: Any) -> Iterable[Any]:
    groups = getattr(catalog, "groups", None) or []
    for g in groups:
        yield from _iter_controls_from_group(g)

    # Catalogs may also have top-level controls
    controls = getattr(catalog, "controls", None) or []
    for c in controls:
        yield c


def _pick_url(control: Any) -> Optional[str]:
    links = getattr(control, "links", None) or []
    for link in links:
        href = getattr(link, "href", None)
        if href:
            return str(href)
    return None


def _normalize_key(oscal_control_id: str) -> str:
    key = str(oscal_control_id).strip()
    if key == "":
        raise ValueError("OSCAL control id is empty")
    if any(ch.isspace() for ch in key):
        raise ValueError(
            f"OSCAL control id contains whitespace and cannot be used as CRML key: {oscal_control_id!r}"
        )
    return key


def oscal_catalog_to_crml_control_catalog(
    oscal_catalog: Any,
    *,
    namespace: str,
    framework: str,
    catalog_id: Optional[str] = None,
    meta_name: Optional[str] = None,
    provenance: Optional[OscalCatalogProvenance] = None,
) -> CRControlCatalog:
    """Convert an OSCAL Catalog into a CRML control catalog (skeleton).

    This intentionally strips detailed statements/parts and only keeps:
    - stable ids (ControlId) derived from OSCAL control ids,
    - OSCAL UUIDs (oscal_uuid),
    - short title (if present),
    - reference URL (first link if present).

    Args:
        namespace: CRML namespace, e.g. "cisv8" or "nist80053r5".
        framework: Human label, e.g. "CIS v8".
        catalog_id: Optional organization-owned catalog identifier.

    Returns:
        CRControlCatalog
    """

    entries: list[ControlCatalogEntry] = []

    for c in _iter_controls(oscal_catalog):
        oscal_id = getattr(c, "id", None)
        if not oscal_id:
            continue

        key = _normalize_key(str(oscal_id))
        control_id = f"{namespace}:{key}"

        title = getattr(c, "title", None)
        url = _pick_url(c)

        oscal_uuid = getattr(c, "uuid", None)
        oscal_uuid_str = str(oscal_uuid) if oscal_uuid is not None else None

        entries.append(
            ControlCatalogEntry.model_validate(
                {
                    "id": control_id,
                    "oscal_uuid": oscal_uuid_str,
                    "title": str(title) if title else None,
                    "url": url,
                }
            )
        )

    description_parts: list[str] = [
        "Imported from OSCAL catalog and stripped to a redistributable skeleton (no standard text)."
    ]
    if provenance is not None:
        if provenance.source_path:
            description_parts.append(f"Source path: {provenance.source_path}")
        if provenance.source_url:
            description_parts.append(f"Source URL: {provenance.source_url}")
        if provenance.license:
            description_parts.append(f"License/terms: {provenance.license}")

    meta = Meta.model_validate(
        {
            "name": meta_name or f"{framework} (imported from OSCAL)",
            "description": "\n".join(description_parts),
        }
    )

    catalog = ControlCatalog.model_validate(
        {
            "id": catalog_id,
            "framework": framework,
            "controls": [e.model_dump(exclude_none=True) for e in entries],
        }
    )

    return CRControlCatalog(
        crml_control_catalog="1.0",
        meta=meta,
        catalog=catalog,
    )
