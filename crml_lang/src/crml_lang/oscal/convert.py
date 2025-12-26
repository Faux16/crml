from __future__ import annotations

import re
from typing import Any, Iterable, Optional

from crml_lang.models.control_catalog_model import ControlCatalogEntry

from .standards.base import OscalControlTextOptions


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


_URL_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")


def _is_url(value: Optional[str]) -> bool:
    if not value:
        return False
    return bool(_URL_RE.match(value.strip()))


def _coerce_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        s = value.strip()
        return s or None
    # Some YAML loaders might parse scalars into non-str types.
    s = str(value).strip()
    return s or None


def _extract_metadata_remarks(catalog: dict[str, Any]) -> Optional[str]:
    metadata = catalog.get("metadata")
    if not isinstance(metadata, dict):
        return None

    remarks = metadata.get("remarks")

    # OSCAL schema: typically a string; be tolerant.
    if isinstance(remarks, list):
        parts: list[str] = []
        for item in remarks:
            s = _coerce_text(item)
            if s:
                parts.append(s)
        return "\n".join(parts) if parts else None

    return _coerce_text(remarks)


def _coerce_prose(value: Any) -> Optional[str]:
    """Coerce an OSCAL prose-like value to text.

    OSCAL schemas typically use strings for prose, but some sources may emit
    lists or non-string scalars.
    """

    if value is None:
        return None
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            s = _coerce_text(item)
            if s:
                parts.append(s)
        return "\n".join(parts) if parts else None
    return _coerce_text(value)


def _iter_oscal_parts(node: Any) -> Iterable[dict[str, Any]]:
    """Yield OSCAL part objects from a control/part subtree."""

    if not isinstance(node, dict):
        return

    parts = node.get("parts")
    if isinstance(parts, list):
        for p in parts:
            if isinstance(p, dict):
                yield p
                yield from _iter_oscal_parts(p)


def _extract_control_prose(
    control: dict[str, Any],
    *,
    options: Optional[OscalControlTextOptions] = None,
) -> Optional[str]:
    """Extract human prose text from an OSCAL control.

    Default (legacy) behavior: include control.prose and all parts[].prose
    recursively.

    When `options.include_part_names` is provided, only include parts whose
    `name` is in that allowlist. This supports standard-specific behavior
    (e.g., SCF: statement + objectives, excluding maturity rubrics).
    """

    prose_parts: list[str] = []

    if options is None or options.include_part_names is None:
        direct = _coerce_prose(control.get("prose"))
        if direct:
            prose_parts.append(direct)

        for part in _iter_oscal_parts(control):
            s = _coerce_prose(part.get("prose"))
            if s:
                prose_parts.append(s)

        return _join_paragraphs(prose_parts)

    if options.include_control_prose:
        direct = _coerce_prose(control.get("prose"))
        if direct:
            prose_parts.append(direct)

    statement_parts: list[str] = []
    other_parts: list[str] = []
    objective_lines: list[str] = []

    allow = {str(n) for n in options.include_part_names}

    for part in _iter_oscal_parts(control):
        name = part.get("name")
        name_str = str(name).strip() if isinstance(name, str) and name.strip() else None
        if not name_str or name_str not in allow:
            continue

        s = _coerce_prose(part.get("prose"))
        if not s:
            continue

        if name_str == "objective":
            oid = _coerce_text(part.get("id"))
            if options.include_objective_ids and oid:
                objective_lines.append(f"{oid}: {s}")
            else:
                objective_lines.append(s)
            continue

        if name_str == "statement":
            statement_parts.append(s)
        else:
            other_parts.append(s)

    prose_parts.extend(statement_parts)

    if objective_lines:
        if options.bullet_objectives:
            block = "\n".join(f"- {ln.strip()}" for ln in objective_lines if ln.strip())
        else:
            block = "\n".join(ln.strip() for ln in objective_lines if ln.strip())

        if options.objective_heading:
            block = f"{options.objective_heading}:\n{block}" if block else options.objective_heading

        if block:
            prose_parts.append(block)

    prose_parts.extend(other_parts)

    return _join_paragraphs(prose_parts)


def _extract_group_prose(group: dict[str, Any]) -> Optional[str]:
    """Extract human prose text from an OSCAL group.

    OSCAL groups may carry prose directly and/or via parts.
    """

    prose_parts: list[str] = []

    direct = _coerce_prose(group.get("prose"))
    if direct:
        prose_parts.append(direct)

    for part in _iter_oscal_parts(group):
        s = _coerce_prose(part.get("prose"))
        if s:
            prose_parts.append(s)

    return _join_paragraphs(prose_parts)


def _join_paragraphs(parts: list[str]) -> Optional[str]:
    cleaned = [p.strip() for p in parts if isinstance(p, str) and p.strip()]
    return "\n\n".join(cleaned) if cleaned else None


_NS_RE = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")


def is_valid_namespace(namespace: str) -> bool:
    """Return True if `namespace` satisfies CRML ControlId namespace constraints."""
    return bool(_NS_RE.match(namespace))


def slug_namespace(text: str) -> str:
    """Convert arbitrary text into a CRML-safe namespace slug."""
    return _slug_namespace(text)


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


def _first_prop_value(node: dict[str, Any], *, name: str) -> Optional[str]:
    props = node.get("props")
    if not isinstance(props, list):
        return None

    for p in props:
        if not isinstance(p, dict):
            continue
        if str(p.get("name", "")).strip() != name:
            continue
        value = _coerce_text(p.get("value"))
        if value:
            return value
    return None


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


def _control_id_from_oscal_id(*, namespace: str, oscal_id: Any) -> Optional[str]:
    if not oscal_id:
        return None
    key = _normalize_key(str(oscal_id))
    return f"{namespace}:{key}"


def _slug_group_id(text: str) -> str:
    """Generate a stable-ish group id if OSCAL group.id is missing.

    This is intentionally simple and conservative; group ids are not used as
    canonical identifiers outside the document.
    """

    s = str(text).strip().lower()
    s = re.sub(r"[^a-z0-9_-]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-_ ")

    if not s or not s[:1].isalpha():
        s = "group"

    return s[:64].strip("-_ ") or "group"


def _oscal_groups_to_crml_groups(
    node: Any, *, namespace: str, include_prose: bool
) -> list[dict[str, Any]]:
    if not isinstance(node, dict):
        return []

    groups = node.get("groups")
    if not isinstance(groups, list):
        return []

    out: list[dict[str, Any]] = []

    for g in groups:
        if not isinstance(g, dict):
            continue

        gid = _coerce_text(g.get("id"))
        oscal_uuid = _coerce_text(g.get("uuid"))
        title = _coerce_text(g.get("title"))
        prose = _extract_group_prose(g) if include_prose else None

        if not gid and title:
            gid = _slug_group_id(title)

        # Direct controls in this group (do not include nested sub-controls).
        control_ids: list[str] = []
        controls = g.get("controls")
        if isinstance(controls, list):
            for c in controls:
                if not isinstance(c, dict):
                    continue
                cid = _control_id_from_oscal_id(namespace=namespace, oscal_id=c.get("id"))
                if cid and cid not in control_ids:
                    control_ids.append(cid)

        # Ensure stable output ordering independent of OSCAL input ordering.
        control_ids.sort()

        nested = _oscal_groups_to_crml_groups(g, namespace=namespace, include_prose=include_prose)

        if not gid:
            # No id and no title to derive one; skip.
            if not nested and not control_ids:
                continue
            gid = "group"

        item: dict[str, Any] = {"id": gid}
        if oscal_uuid:
            item["oscal_uuid"] = oscal_uuid
        if title:
            item["title"] = title
        if prose:
            item["description"] = prose
        if control_ids:
            item["control_ids"] = control_ids
        if nested:
            item["groups"] = nested

        out.append(item)

    # Ensure stable ordering of groups at each level.
    out.sort(
        key=lambda d: (
            str(d.get("id") or ""),
            str(d.get("title") or ""),
            str(d.get("oscal_uuid") or ""),
        )
    )

    return out


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
    include_prose: bool = True,
    control_text_options: Optional[OscalControlTextOptions] = None,
) -> dict[str, Any]:
    """Convert an OSCAL Catalog document into a CRML skeleton control catalog.

    Output is intentionally metadata-only (no standard text).
    """

    catalog = _get_catalog_root(oscal_doc)
    catalog_oscal_uuid = _coerce_text(catalog.get("uuid"))

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

        # Some OSCAL sources (including certain catalog publishers) store the stable UUID
        # in a prop like {name: "alt-identifier", value: "..."} instead of control.uuid.
        oscal_uuid_str = _coerce_text(c.get("uuid")) or _first_prop_value(c, name="alt-identifier")

        title = c.get("title")
        title_str = str(title).strip() if isinstance(title, str) and title.strip() else None

        prose = _extract_control_prose(c, options=control_text_options) if include_prose else None

        url = _first_link_href(c)

        entry = ControlCatalogEntry(
            id=control_id,
            oscal_uuid=oscal_uuid_str,
            title=title_str,
            description=prose,
            url=url,
        )
        controls_out.append(entry.model_dump(by_alias=True, exclude_none=True))

    # Ensure stable ordering of controls (and therefore stable YAML diffs) regardless
    # of OSCAL group nesting or input file ordering.
    controls_out.sort(key=lambda d: str(d.get("id") or ""))

    groups_out = _oscal_groups_to_crml_groups(catalog, namespace=namespace, include_prose=include_prose)

    description_parts: list[str] = []

    # Prefer OSCAL-provided human remarks as the primary description.
    remarks = _extract_metadata_remarks(catalog)
    if remarks:
        description_parts.append(remarks)

    if include_prose:
        description_parts.append("Imported from OSCAL.")
    else:
        # Redistribution/skeleton note for safety and clarity.
        description_parts.append(
            "Imported from OSCAL and stripped to a redistributable skeleton (no standard text)."
        )
    if license_terms:
        description_parts.append(f"Terms: {license_terms}")

    description = _join_paragraphs(description_parts)

    meta: dict[str, Any] = {
        "name": meta_name or f"{framework} (imported from OSCAL)",
        "description": description,
    }

    # Preserve provenance when we have a URL, but do not emit local paths.
    if _is_url(source_url):
        meta["reference"] = str(source_url).strip()

    return {
        "crml_control_catalog": "1.0",
        "meta": meta,
        "catalog": {
            "id": catalog_id,
            "oscal_uuid": catalog_oscal_uuid,
            "framework": framework,
            "controls": controls_out,
            **({"groups": groups_out} if groups_out else {}),
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

    description_parts: list[str] = []
    remarks = _extract_metadata_remarks(catalog)
    if remarks:
        description_parts.append(remarks)
    description_parts.append(
        "Generated from an OSCAL catalog as an assessment template (no posture values in OSCAL catalog)."
    )
    if license_terms:
        description_parts.append(f"Terms: {license_terms}")

    description = _join_paragraphs(description_parts)

    meta: dict[str, Any] = {
        "name": meta_name or f"{framework} assessment (imported from OSCAL)",
        "description": description,
    }
    if _is_url(source_url):
        meta["reference"] = str(source_url).strip()

    return {
        "crml_assessment": "1.0",
        "meta": meta,
        "assessment": {
            "id": assessment_id,
            "framework": framework,
            "assessments": assessments_out,
        },
    }
