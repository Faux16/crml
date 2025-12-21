"""Deterministic planning pipeline.

This package produces execution-ready artifacts from CRML documents without
running any Monte Carlo simulation.

Key outputs:
- `plan_portfolio(...)` -> `PlanReport` / `PortfolioExecutionPlan`
- `plan_bundle(...)` -> `PlanReport` / `PortfolioExecutionPlan`

The data contracts (schemas/models) remain in `crml_lang`.
"""

from .portfolio_planner import (
    PlanMessage,
    PlanReport,
    PortfolioExecutionPlan,
    ResolvedScenario,
    ResolvedScenarioControl,
    plan_bundle,
    plan_portfolio,
)

__all__ = [
    "PlanMessage",
    "PlanReport",
    "PortfolioExecutionPlan",
    "ResolvedScenario",
    "ResolvedScenarioControl",
    "plan_bundle",
    "plan_portfolio",
]
