from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class RiskToleranceMetric(str, Enum):
    """Metric identifier used by `RiskTolerance`.

    Values are chosen to match common CRML measure ids/parameters.
    """

    MAX_EAL = "max_eal"
    MAX_VAR_95 = "max_var_95"
    MAX_VAR_99 = "max_var_99"
    MAX_VAR_999 = "max_var_999"
    MAX_CVAR_95 = "max_cvar_95"
    MAX_CVAR_99 = "max_cvar_99"


class RiskTolerance(BaseModel):
    metric: RiskToleranceMetric = Field(
        ...,
        description=(
            "Risk-tolerance metric identifier. Example: 'max_var_95' expresses a maximum allowed VaR at 95%."
        ),
    )
    threshold: float = Field(
        ...,
        ge=0.0,
        description=(
            "Numeric threshold for the selected metric. Typically expressed in the result currency unit."
        ),
    )

    currency: Optional[str] = Field(
        None,
        min_length=3,
        max_length=3,
        description=(
            "Optional ISO 4217 currency code for the threshold (e.g. 'USD', 'EUR'). "
            "If omitted, consumers may assume the simulation output currency."
        ),
    )
