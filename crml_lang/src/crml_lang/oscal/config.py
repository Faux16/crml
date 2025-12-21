from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any, Literal, Optional, cast

import importlib.resources

from crml_lang.yamlio import load_yaml_mapping_from_str

from crml_lang.models.meta_tokens import ALLOWED_COMPANY_SIZE_TOKENS, ALLOWED_INDUSTRY_TOKENS

from .locale import OscalLocale


OscalKind = Literal["catalog", "assets", "assessment", "mapping"]
OscalMappingType = Literal["control_relationships", "attack_control_relationships"]


@dataclass(frozen=True, slots=True)
class OscalEndpoint:
    id: str
    description: str
    kind: OscalKind

    # --- source (exactly one of these must be set) ---
    url: Optional[str] = None
    path: Optional[str] = None

    # --- kind: assets ---
    # Creates a CRML portfolio-like asset inventory from an OSCAL source.
    portfolio_meta_name: Optional[str] = None
    default_cardinality: int = 1

    # --- kind: mapping ---
    # Generates a CRML relationships document.
    mapping_type: Optional[OscalMappingType] = None

    # --- common ---
    timeout_seconds: float = 30.0

    # --- common locale metadata (optional) ---
    # These mirror CRML's `meta.locale` conventions: `regions` and `countries`.
    # Backwards-compatible YAML keys `region`/`country` are also accepted.
    regions: Optional[list[str]] = None
    countries: Optional[list[str]] = None
    locale: Optional[OscalLocale] = None

    # --- common metadata copied into generated CRML artifacts (optional) ---
    # `meta_overrides` is a CRML-shaped `meta` mapping which will be merged into
    # generated CRML artifacts (control catalogs, etc.).
    #
    # Supported via:
    # - `meta: { industries: [...], company_sizes: [...], locale: {regions: [...], countries: [...]}, ... }`
    # - Backwards-compatible top-level keys: `industries`, `company_sizes`, `regions`/`countries`.
    industries: Optional[list[str]] = None
    company_sizes: Optional[list[str]] = None
    meta_overrides: Optional[dict[str, Any]] = None

    # --- kind: catalog (optional overrides) ---
    namespace_override: Optional[str] = None
    framework_override: Optional[str] = None
    catalog_id: Optional[str] = None
    meta_name: Optional[str] = None

    @property
    def source(self) -> str:
        if self.url:
            return self.url
        if self.path:
            return self.path
        # Should be unreachable due to parsing validation.
        return ""


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


def _optional_str(item: dict[str, Any], key: str) -> Optional[str]:
    raw = item.get(key)
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


def _parse_string_list(*, endpoint_id: str, key: str, raw: Any) -> list[str]:
    if isinstance(raw, str):
        s = raw.strip()
        return [s] if s else []

    if not isinstance(raw, list):
        raise ValueError(
            f"OSCAL endpoint {endpoint_id!r} field {key!r} must be a string or a list of strings"
        )

    out: list[str] = []
    for x in raw:
        if x is None:
            continue
        if not isinstance(x, str):
            raise ValueError(
                f"OSCAL endpoint {endpoint_id!r} field {key!r} must contain only strings"
            )
        s = x.strip()
        if s:
            out.append(s)
    return out


def _validate_industries(*, endpoint_id: str, values: list[str]) -> None:
    for v in values:
        if v not in ALLOWED_INDUSTRY_TOKENS:
            raise ValueError(
                f"OSCAL endpoint {endpoint_id!r} field 'industries' contains invalid token {v!r}. "
                f"Allowed: {list(ALLOWED_INDUSTRY_TOKENS)!r}"
            )


def _validate_company_sizes(*, endpoint_id: str, values: list[str]) -> None:
    for v in values:
        if v not in ALLOWED_COMPANY_SIZE_TOKENS:
            raise ValueError(
                f"OSCAL endpoint {endpoint_id!r} field 'company_sizes' contains invalid token {v!r}. "
                f"Allowed: {list(ALLOWED_COMPANY_SIZE_TOKENS)!r}"
            )


def _optional_str_list(item: dict[str, Any], *, endpoint_id: str, key: str) -> Optional[list[str]]:
    raw = item.get(key)
    if raw is None:
        return None
    values = _parse_string_list(endpoint_id=endpoint_id, key=key, raw=raw)
    return values or None


def _parse_kind(item: dict[str, Any], *, default_kind: Optional[OscalKind]) -> OscalKind:
    kind_raw = _optional_str(item, "kind") or (default_kind or "catalog")
    if kind_raw not in ("catalog", "assets", "assessment", "mapping"):
        raise ValueError(f"Unsupported OSCAL endpoint kind: {kind_raw!r}")
    return cast(OscalKind, kind_raw)


def _parse_source(
    item: dict[str, Any],
    *,
    endpoint_id: str,
    base_dir: Optional[Path],
) -> tuple[Optional[str], Optional[str]]:
    url = _optional_str(item, "url")
    path_raw = _optional_str(item, "path")

    if (url is None) == (path_raw is None):
        raise ValueError(f"OSCAL endpoint {endpoint_id!r} must set exactly one of: url, path")

    if path_raw is None:
        return url, None

    p = Path(path_raw)
    if base_dir is not None and not p.is_absolute():
        p = base_dir / p
    return None, str(p.resolve())


def _parse_endpoint_item(
    item: Any,
    *,
    default_kind: Optional[OscalKind] = None,
    base_dir: Optional[Path] = None,
) -> OscalEndpoint:
    if not isinstance(item, dict):
        raise ValueError("Each OSCAL endpoint must be a mapping")

    typed = cast(dict[str, Any], item)

    endpoint_id = str(typed.get("id", "")).strip()
    if not endpoint_id:
        raise ValueError("OSCAL endpoint is missing required field 'id'")

    description = str(typed.get("description", "")).strip()
    if not description:
        raise ValueError(f"OSCAL endpoint {endpoint_id!r} is missing required field 'description'")

    url, path = _parse_source(typed, endpoint_id=endpoint_id, base_dir=base_dir)
    kind = _parse_kind(typed, default_kind=default_kind)
    timeout_seconds = _parse_timeout_seconds(endpoint_id, typed.get("timeout_seconds", 30.0))

    portfolio_meta_name: Optional[str] = None
    default_cardinality = 1
    mapping_type: Optional[OscalMappingType] = None

    namespace_override = _optional_str(typed, "namespace")
    framework_override = _optional_str(typed, "framework")
    catalog_id = _optional_str(typed, "catalog_id")
    meta_name = _optional_str(typed, "meta_name")

    regions = _optional_str_list(typed, endpoint_id=endpoint_id, key="regions")
    countries = _optional_str_list(typed, endpoint_id=endpoint_id, key="countries")
    industries = _optional_str_list(typed, endpoint_id=endpoint_id, key="industries")
    if industries is not None:
        _validate_industries(endpoint_id=endpoint_id, values=industries)

    company_sizes = _optional_str_list(typed, endpoint_id=endpoint_id, key="company_sizes")
    if company_sizes is not None:
        _validate_company_sizes(endpoint_id=endpoint_id, values=company_sizes)

    meta_overrides_raw = typed.get("meta")
    if meta_overrides_raw is None:
        meta_overrides: dict[str, Any] = {}
    elif not isinstance(meta_overrides_raw, dict):
        raise ValueError(f"OSCAL endpoint {endpoint_id!r} field 'meta' must be a mapping")
    else:
        meta_overrides = dict(meta_overrides_raw)

    meta_industries_raw = meta_overrides.get("industries")
    if meta_industries_raw is not None:
        meta_industries = _parse_string_list(
            endpoint_id=endpoint_id, key="meta.industries", raw=meta_industries_raw
        )
        _validate_industries(endpoint_id=endpoint_id, values=meta_industries)
        meta_overrides["industries"] = meta_industries

    meta_company_sizes_raw = meta_overrides.get("company_sizes")
    if meta_company_sizes_raw is not None:
        meta_company_sizes = _parse_string_list(
            endpoint_id=endpoint_id, key="meta.company_sizes", raw=meta_company_sizes_raw
        )
        _validate_company_sizes(endpoint_id=endpoint_id, values=meta_company_sizes)
        meta_overrides["company_sizes"] = meta_company_sizes

    # Backwards-compatible singular fields.
    region_single = _optional_str(typed, "region")
    country_single = _optional_str(typed, "country")
    if region_single and not regions:
        regions = [region_single]
    if country_single and not countries:
        countries = [country_single]

    # If the endpoint provides a CRML-shaped meta.locale, normalize its regions/countries
    # while preserving any extra locale keys.
    locale_from_meta: Optional[OscalLocale] = None
    meta_locale_raw = meta_overrides.get("locale")
    if meta_locale_raw is not None:
        if not isinstance(meta_locale_raw, dict):
            raise ValueError(
                f"OSCAL endpoint {endpoint_id!r} field 'meta.locale' must be a mapping"
            )

        meta_locale = dict(meta_locale_raw)
        meta_regions = meta_locale.get("regions")
        meta_countries = meta_locale.get("countries")
        # Only normalize if either is provided.
        if meta_regions is not None or meta_countries is not None:
            locale_from_meta = OscalLocale(
                regions=_parse_string_list(endpoint_id=endpoint_id, key="meta.locale.regions", raw=meta_regions)
                if meta_regions is not None
                else [],
                countries=_parse_string_list(endpoint_id=endpoint_id, key="meta.locale.countries", raw=meta_countries)
                if meta_countries is not None
                else [],
            )
            meta_locale["regions"] = locale_from_meta.regions
            meta_locale["countries"] = locale_from_meta.countries
            meta_overrides["locale"] = meta_locale

    # Prefer explicit meta.locale for the endpoint locale object; otherwise derive it from
    # top-level regions/countries.
    locale = locale_from_meta
    if locale is None and (regions or countries):
        locale = OscalLocale(regions=regions or [], countries=countries or [])

    # If top-level industries is set but meta.industries is not, populate it.
    if industries is not None and "industries" not in meta_overrides:
        meta_overrides["industries"] = industries

    # If top-level company_sizes is set but meta.company_sizes is not, populate it.
    if company_sizes is not None and "company_sizes" not in meta_overrides:
        meta_overrides["company_sizes"] = company_sizes

    # If locale is derived from top-level regions/countries and meta.locale is not set,
    # populate meta.locale in CRML shape.
    if locale is not None and "locale" not in meta_overrides:
        meta_overrides["locale"] = locale.model_dump(exclude_none=True)

    meta_overrides_or_none: Optional[dict[str, Any]] = meta_overrides or None

    if kind == "catalog" and not catalog_id:
        raise ValueError(
            f"OSCAL catalog endpoint {endpoint_id!r} is missing required field 'catalog_id'"
        )

    if kind == "assets":
        portfolio_meta_name, default_cardinality = _parse_assets_fields(typed, endpoint_id)
    elif kind == "mapping":
        mapping_type = _parse_mapping_type(typed, endpoint_id)

    return OscalEndpoint(
        id=endpoint_id,
        description=description,
        kind=kind,
        url=url,
        path=path,
        portfolio_meta_name=portfolio_meta_name,
        default_cardinality=default_cardinality,
        mapping_type=mapping_type,
        timeout_seconds=timeout_seconds,
        regions=regions,
        countries=countries,
        locale=locale,
        industries=industries,
        company_sizes=company_sizes,
        meta_overrides=meta_overrides_or_none,
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

        Schema:
        - catalogs: []
        - assets: []
        - assessments: []
        - mappings: []
    """

    return load_endpoints_from_file(None)


def load_endpoints_from_file(
    path: Optional[str],
    *,
    include_builtin: bool = True,
    include_env: bool = True,
) -> list[OscalEndpoint]:
    """Load OSCAL endpoints.

    Merge order (later sources override earlier by endpoint id):
    - built-in package data file `api-endpoints.yaml` (if include_builtin)
    - `path` (if provided)
    - optional external endpoint files provided via `CRML_OSCAL_ENDPOINTS_PATH` (if include_env)

    Schema:
    - catalogs: []
    - assets: []
    - assessments: []
    - mappings: []
    """

    merged: dict[str, OscalEndpoint] = {}

    def _merge_endpoint_list(
        raw: dict[str, Any],
        *,
        key: str,
        default_kind: Optional[OscalKind],
        base_dir: Optional[Path],
    ) -> bool:
        items = raw.get(key)
        if items is None:
            return False
        if not isinstance(items, list):
            raise ValueError(f"OSCAL endpoints config field {key!r} must be a list")
        for item in items:
            e = _parse_endpoint_item(item, default_kind=default_kind, base_dir=base_dir)
            merged[e.id] = e
        return True

    def merge_text(text: str, *, base_dir: Optional[Path]) -> None:
        raw = load_yaml_mapping_from_str(text)

        _merge_endpoint_list(raw, key="catalogs", default_kind="catalog", base_dir=base_dir)
        _merge_endpoint_list(raw, key="assets", default_kind="assets", base_dir=base_dir)
        _merge_endpoint_list(raw, key="assessments", default_kind="assessment", base_dir=base_dir)
        _merge_endpoint_list(raw, key="mappings", default_kind="mapping", base_dir=base_dir)

    if include_builtin:
        merge_text(_read_endpoints_yaml_text(), base_dir=None)

    if path:
        pp = Path(path)
        merge_text(pp.read_text(encoding="utf-8"), base_dir=pp.parent)

    if include_env:
        for p in _iter_external_endpoint_paths():
            pp = Path(p)
            merge_text(pp.read_text(encoding="utf-8"), base_dir=pp.parent)

    return list(merged.values())
