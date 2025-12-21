from __future__ import annotations

import re
from typing import Any, Iterable, Optional

from crml_lang.models.control_catalog_model import ControlCatalogEntry


def infer_namespace_and_framework(oscal_doc: dict[str, Any]) -> tuple[str, str]:
    """Infer CRML `namespace` and `framework` defaults from an OSCAL document.

    - `framework` is a human label; we prefer OSCAL metadata title.
    - `namespace` must satisfy CRML ControlId constraints; we derive a slug.
    """

    catalog = _get_catalog_root(oscal_doc)
    framework = _extract_title(catalog) or "OSCAL"
    namespace = _slug_namespace(framework)
    return namespace, framework


def _extract_title(catalog: dict[str, Any]) -> Optional[str]:
    metadata = catalog.get("metadata")
    if isinstance(metadata, dict):
        title = metadata.get("title")
        if isinstance(title, str) and title.strip():
            return title.strip()

    title = catalog.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()

    return None


_NS_RE = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")


def _slug_namespace(text: str) -> str:
    s = str(text).strip().lower()
    s = re.sub(r"[^a-z0-9_-]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-_ ")

    if not s or not s[:1].isalpha():
        s = "oscal"

    s = s[:32].strip("-_ ")
    if not _NS_RE.match(s):
        return "oscal"
    return s


def _normalize_key(oscal_control_id: str) -> str:
    key = str(oscal_control_id).strip()
    if not key:
        raise ValueError("OSCAL control id is empty")
    if any(c.isspace() for c in key):
        raise ValueError(
            f"OSCAL control id contains whitespace and cannot be used as CRML key: {oscal_control_id!r}"
        )
    return key


def _first_link_href(control: dict[str, Any]) -> Optional[str]:
    links = control.get("links")
    if not isinstance(links, list):
        return None

    hrefs: list[str] = []
    for l in links:
        if not isinstance(l, dict):
            continue
        href = l.get("href")
        if isinstance(href, str) and href.strip():
            hrefs.append(href.strip())

    return hrefs[0] if hrefs else None


def _iter_oscal_controls(node: Any) -> Iterable[dict[str, Any]]:
    """Yield OSCAL control objects from a catalog-like subtree.

    OSCAL catalogs can contain controls at the root and inside nested groups.
    Controls can also contain nested sub-controls.

    This is intentionally schema-tolerant: we only read ids/titles/uuids/links.
    """

    if not isinstance(node, dict):
        return

    controls = node.get("controls")
    if isinstance(controls, list):
        for c in controls:
            if isinstance(c, dict):
                yield c
                yield from _iter_oscal_controls(c)

    groups = node.get("groups")
    if isinstance(groups, list):
        for g in groups:
            if isinstance(g, dict):
                yield from _iter_oscal_controls(g)


def _get_catalog_root(oscal_doc: dict[str, Any]) -> dict[str, Any]:
    if "catalog" in oscal_doc and isinstance(oscal_doc["catalog"], dict):
        return oscal_doc["catalog"]
    return oscal_doc


def oscal_catalog_to_crml_control_catalog(
    oscal_doc: dict[str, Any],
    *,
    namespace: str,
    framework: str,
    catalog_id: Optional[str] = None,
    meta_name: Optional[str] = None,
    source_url: Optional[str] = None,
    license_terms: Optional[str] = None,
) -> dict[str, Any]:
    """Convert an OSCAL Catalog document into a CRML skeleton control catalog.

    Output is intentionally metadata-only (no standard text).
    """

    catalog = _get_catalog_root(oscal_doc)

    controls_out: list[dict[str, Any]] = []
    seen: set[str] = set()

    for c in _iter_oscal_controls(catalog):
        oscal_id = c.get("id")
        if not oscal_id:
            continue

        key = _normalize_key(str(oscal_id))
        control_id = f"{namespace}:{key}"
        if control_id in seen:
            continue
        seen.add(control_id)

        oscal_uuid = c.get("uuid")
        oscal_uuid_str = str(oscal_uuid) if oscal_uuid is not None else None

        title = c.get("title")
        title_str = str(title).strip() if isinstance(title, str) and title.strip() else None

        url = _first_link_href(c)

        entry = ControlCatalogEntry(
            id=control_id,
            oscal_uuid=oscal_uuid_str,
            title=title_str,
            url=url,
        )
        controls_out.append(entry.model_dump(by_alias=True, exclude_none=True))

    description_lines: list[str] = [
        "Imported from OSCAL and stripped to a redistributable skeleton (no standard text)."
    ]
    if source_url:
        description_lines.append(f"Source: {source_url}")
    if license_terms:
        description_lines.append(f"Terms: {license_terms}")

    return {
        "crml_control_catalog": "1.0",
        "meta": {
            "name": meta_name or f"{framework} (imported from OSCAL)",
            "description": "\n".join(description_lines),
        },
        "catalog": {
            "id": catalog_id,
            "framework": framework,
            "controls": controls_out,
        },
    }


def oscal_catalog_to_crml_assessment(
    oscal_doc: dict[str, Any],
    *,
    namespace: str,
    framework: str,
    assessment_id: Optional[str] = None,
    meta_name: Optional[str] = None,
    source_url: Optional[str] = None,
    license_terms: Optional[str] = None,
    default_scf_cmm_level: int = 0,
) -> dict[str, Any]:
    """Create a CRML assessment template from an OSCAL Catalog.

    Since OSCAL catalogs do not carry organization-specific posture values,
    assessments are generated with a default SCF CMM level (0 by default).
    """

    if default_scf_cmm_level < 0 or default_scf_cmm_level > 5:
        raise ValueError("default_scf_cmm_level must be within 0..5")

    catalog = _get_catalog_root(oscal_doc)

    assessments_out: list[dict[str, Any]] = []
    seen: set[str] = set()

    for c in _iter_oscal_controls(catalog):
        oscal_id = c.get("id")
        if not oscal_id:
            continue

        key = _normalize_key(str(oscal_id))
        control_id = f"{namespace}:{key}"
        if control_id in seen:
            continue
        seen.add(control_id)

        oscal_uuid = c.get("uuid")
        oscal_uuid_str = str(oscal_uuid) if oscal_uuid is not None else None

        assessments_out.append(
            {
                "id": control_id,
                "oscal_uuid": oscal_uuid_str,
                "scf_cmm_level": default_scf_cmm_level,
            }
        )

    description_lines: list[str] = [
        "Generated from an OSCAL catalog as an assessment template (no posture values in OSCAL catalog)."
    ]
    if source_url:
        description_lines.append(f"Source: {source_url}")
    if license_terms:
        description_lines.append(f"Terms: {license_terms}")

    return {
        "crml_assessment": "1.0",
        "meta": {
            "name": meta_name or f"{framework} assessment (imported from OSCAL)",
            "description": "\n".join(description_lines),
        },
        "assessment": {
            "id": assessment_id,
            "framework": framework,
            "assessments": assessments_out,
        },
    }
