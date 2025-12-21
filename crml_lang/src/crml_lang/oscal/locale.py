from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from crml_lang.models.meta_tokens import ALLOWED_REGION_TOKENS, ISO3166_1_ALPHA2_PATTERN


_COUNTRY_RE = re.compile(ISO3166_1_ALPHA2_PATTERN)


class OscalLocale(BaseModel):
    """Locale metadata derived from OSCAL endpoint configuration.

    This is intentionally small and validation-focused. It is written into
    generated CRML artifacts under `meta.locale`.
    """

    regions: list[str] = Field(
        default_factory=list,
        description=(
            "List of region tokens (lowercase, e.g. 'all', 'world', 'europe', 'north-america'). "
            "Matches CRML's `meta.locale.regions` convention."
        ),
    )
    countries: list[str] = Field(
        default_factory=list,
        description=(
            "List of ISO 3166-1 alpha-2 country codes (e.g. 'DE', 'US'). "
            "Matches CRML's `meta.locale.countries` convention."
        ),
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("regions", mode="before")
    @classmethod
    def _validate_regions(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            items = [v]
        elif isinstance(v, list):
            items = v
        else:
            raise TypeError("regions must be a string or a list of strings")

        out: list[str] = []
        for item in items:
            if not isinstance(item, str):
                raise TypeError("regions entries must be strings")
            s = item.strip()
            if not s:
                raise ValueError("region token must be a non-empty string")
            if s not in ALLOWED_REGION_TOKENS:
                raise ValueError(
                    f"region token {s!r} is not allowed. Allowed: {list(ALLOWED_REGION_TOKENS)!r}"
                )
            out.append(s)
        return out

    @field_validator("countries", mode="before")
    @classmethod
    def _validate_countries(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            items = [v]
        elif isinstance(v, list):
            items = v
        else:
            raise TypeError("countries must be a string or a list of strings")

        out: list[str] = []
        for item in items:
            if not isinstance(item, str):
                raise TypeError("countries entries must be strings")
            s = item.strip()
            if not s:
                raise ValueError("country code must be a non-empty string")
            if not _COUNTRY_RE.match(s):
                raise ValueError("country code must be ISO 3166-1 alpha-2 (e.g. 'DE')")
            out.append(s)
        return out

    @model_validator(mode="after")
    def _validate_pair(self) -> "OscalLocale":
        # CRML convention: regions are strongly recommended.
        # Endpoint rule: allow regions without countries, but forbid countries without regions.
        if self.countries and not self.regions:
            raise ValueError("locale must not set countries without also setting at least one region")
        return self
