# Engine capabilities: Controls

Controls are defined in CRML scenarios (what the scenario assumes exists) and implemented/measured in portfolios (what the organization has).

This page documents what the reference engine does with control data during portfolio execution.

---

## Where controls appear

- Scenario controls: `scenario.controls` (list of control ids referenced by the scenario)
- Portfolio controls: `portfolio.controls` (implementation effectiveness, coverage, reliability, affects)
- Optional assessments + catalogs: `portfolio.assessments`, `portfolio.control_catalogs`

Schema docs:

- Scenario: [Language/Schemas/Scenario](../../Language/Schemas/Scenario.md)
- Portfolio: [Language/Schemas/Portfolio](../../Language/Schemas/Portfolio.md)
- Assessment: [Language/Schemas/Assessment](../../Language/Schemas/Assessment.md)
- Control catalog: [Language/Schemas/Control-Catalog](../../Language/Schemas/Control-Catalog.md)

---

## Control resolution (planning)

Before simulation, the engine creates a **portfolio execution plan** that resolves each scenario control to an “effective” control payload.

Key behaviors implemented in the portfolio planner:

- Portfolio `controls` take precedence.
- If assessments are provided, the planner can derive effectiveness from SCF CMM levels using a non-linear mapping.
- The planner emits errors if:
  - a referenced control id isn’t present in the referenced catalogs (when catalogs are provided)
  - copula targets reference unknown control ids

Implementation: [crml_engine/src/crml_engine/pipeline/portfolio_planner.py](../../../crml_engine/src/crml_engine/pipeline/portfolio_planner.py)
Implementation: `crml_engine/src/crml_engine/pipeline/portfolio_planner.py`

---

## How controls affect simulation

During simulation, each resolved control contributes a multiplicative reduction:

- reduction = `implementation_effectiveness × coverage × state`
- multiplier = `1 - reduction`

`state` is per-run and is `1` when the control is “up” for that run.

Controls can affect:

- `frequency`
- `severity`
- `both`

Implementation: `_control_multipliers_for_scenario` in [crml_engine/src/crml_engine/runtime.py](../../../crml_engine/src/crml_engine/runtime.py)
Implementation: `_control_multipliers_for_scenario` in `crml_engine/src/crml_engine/runtime.py`

---

## Reliability and correlated control state

If `reliability` is provided, the engine samples a per-run Bernoulli state for each control.

If the portfolio dependency includes a Gaussian copula over `control:<id>:state` targets, the engine correlates those Bernoulli samples via copula uniforms.

See: [Portfolio execution](Portfolio-Execution.md)
