from __future__ import annotations

from typing import Annotated, Any, Final
from enum import Enum

from pydantic.json_schema import WithJsonSchema


class RegionToken(str, Enum):
    """Canonical CRML region tokens.

    Values are strict and must match exactly.
    """

    ALL = "all"
    WORLD = "world"
    NORTH_AMERICA = "north-america"
    LATIN_AMERICA = "latin-america"
    EUROPE = "europe"
    MIDDLE_EAST_AFRICA = "middle-east-africa"
    ASIA_PACIFIC = "asia-pacific"
    OCEANIA = "oceania"


class IndustryToken(str, Enum):
    """Canonical CRML industry tokens.

    Values are strict and must match exactly.
    """

    ALL = "all"
    FINANCIAL_SERVICES = "financial-services"
    HEALTHCARE = "healthcare"
    MANUFACTURING = "manufacturing"
    RETAIL_WHOLESALE = "retail-wholesale"
    TECHNOLOGY = "technology"
    PROFESSIONAL_SERVICES = "professional-services"
    EDUCATION = "education"
    GOVERNMENT = "government"
    ENERGY_UTILITIES = "energy-utilities"
    TRANSPORTATION_LOGISTICS = "transportation-logistics"
    MEDIA_ENTERTAINMENT = "media-entertainment"
    CONSTRUCTION_REAL_ESTATE = "construction-real-estate"
    HOSPITALITY_FOOD_SERVICE = "hospitality-food-service"
    NONPROFIT_NGO = "nonprofit-ngo"


class CompanySizeToken(str, Enum):
    """Canonical CRML company size tokens.

    Values are strict and must match exactly.
    """

    ALL = "all"
    MICRO = "micro"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"


ALLOWED_REGION_TOKENS: Final[tuple[str, ...]] = tuple(x.value for x in RegionToken)
ALLOWED_INDUSTRY_TOKENS: Final[tuple[str, ...]] = tuple(x.value for x in IndustryToken)
ALLOWED_COMPANY_SIZE_TOKENS: Final[tuple[str, ...]] = tuple(x.value for x in CompanySizeToken)


ISO3166_1_ALPHA2_PATTERN: Final[str] = r"^[A-Z]{2}$"


ISO3166_1_ALPHA2_SCHEMA: Final[dict[str, Any]] = {
    "type": "string",
    "title": "iso3166_1_alpha2",
    "description": "ISO 3166-1 alpha-2 country code (uppercase).",
    "pattern": ISO3166_1_ALPHA2_PATTERN,
}


LOCALE_JSON_SCHEMA: Final[dict[str, Any]] = {
    "type": "object",
    "title": "Locale",
    "description": "Optional locale/region information and arbitrary locale metadata.",
    "additionalProperties": True,
    "properties": {
        "regions": {
            "anyOf": [
                {
                    "type": "array",
                    "items": {"type": "string", "enum": list(ALLOWED_REGION_TOKENS)},
                },
                {"type": "null"},
            ],
            "default": None,
            "description": "Optional list of region tokens.",
            "title": "Regions",
        },
        "countries": {
            "anyOf": [
                {
                    "type": "array",
                    "items": dict(ISO3166_1_ALPHA2_SCHEMA),
                },
                {"type": "null"},
            ],
            "default": None,
            "description": "Optional list of ISO 3166-1 alpha-2 country codes.",
            "title": "Countries",
        },
    },
}


LocaleDict = Annotated[dict[str, Any], WithJsonSchema(LOCALE_JSON_SCHEMA)]
