from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Optional
from urllib.request import Request, urlopen

from .errors import OscalFetchError, OscalParseError

from crml_lang.yamlio import load_yaml_mapping_from_path, load_yaml_mapping_from_str


def _ensure_mapping(parsed: Any) -> dict[str, Any]:
    if not isinstance(parsed, dict):
        raise ValueError("OSCAL document must be a mapping/object at top-level")
    return parsed


def _parse_oscal_text(text: str, *, source_label: str) -> dict[str, Any]:
    try:
        return _ensure_mapping(json.loads(text))
    except Exception:
        try:
            return load_yaml_mapping_from_str(text)
        except Exception as e:
            raise OscalParseError(source_label, str(e)) from e


def _load_oscal_from_path(p: Path) -> dict[str, Any]:
    suffix = p.suffix.lower()
    if suffix in (".yaml", ".yml"):
        return load_yaml_mapping_from_path(str(p))
    if suffix == ".json":
        with open(p, "r", encoding="utf-8") as f:
            return _ensure_mapping(json.load(f))

    # Fallback: try JSON, then YAML.
    return _parse_oscal_text(p.read_text(encoding="utf-8"), source_label=str(p))


def _load_oscal_from_url(
    url: str,
    timeout_seconds: float,
    *,
    user_agent: Optional[str],
    accept: str,
    source_label: str,
) -> dict[str, Any]:
    headers = {"Accept": accept}
    if user_agent:
        headers["User-Agent"] = user_agent

    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=timeout_seconds) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            text = resp.read().decode(charset, errors="replace")
    except Exception as e:
        raise OscalFetchError(url, str(e)) from e

    # URL content is expected to be JSON, but allow YAML.
    return _parse_oscal_text(text, source_label=source_label)


def load_oscal_document(
    *,
    path: Optional[str] = None,
    url: Optional[str] = None,
    data: Optional[Mapping[str, Any]] = None,
    timeout_seconds: float = 30.0,
    user_agent: Optional[str] = None,
    accept: str = "application/json, application/yaml, text/yaml, */*",
    source_label: Optional[str] = None,
) -> dict[str, Any]:
    """Load an OSCAL document from a path, URL, or pre-parsed mapping.

    OSCAL supports JSON and YAML encodings.

    Exactly one of (path, url, data) must be provided.
    """

    if sum(x is not None for x in (path, url, data)) != 1:
        raise ValueError("Provide exactly one of: path, url, data")

    if data is not None:
        return dict(data)

    if path is not None:
        return _load_oscal_from_path(Path(path))

    assert url is not None
    return _load_oscal_from_url(
        url,
        timeout_seconds,
        user_agent=user_agent,
        accept=accept,
        source_label=source_label or url,
    )
