# Engine capabilities: Supported models

This page documents what the **reference engine** (`crml_engine`) supports today.

For the portable language contract, see: [CRML Specification (Overview)](../../Reference/CRML-Specification.md)

---

## Inputs

The reference engine executes these CRML document types:

- `crml_scenario: "1.0"`
- `crml_portfolio: "1.0"`
- `crml_portfolio_bundle: "1.0"`

---

## Scenario frequency models

Implemented in `crml_engine/src/crml_engine/simulation/frequency.py`.

Supported `scenario.frequency.model` identifiers:

- `poisson`
- `gamma`
- `hierarchical_gamma_poisson`

The portable basis semantics (`per_organization_per_year` vs `per_asset_unit_per_year`) are defined in [CRML Specification (Overview)](../../Reference/CRML-Specification.md).

---

## Scenario severity models

Implemented in `crml_engine/src/crml_engine/simulation/severity.py`.

Supported `scenario.severity.model` identifiers:

- `lognormal`
- `gamma`
- `mixture` (limited; see below)

### Mixture severity limitation (important)

The current reference implementation of `mixture` severity only uses the **first component** and ignores mixture weights.

This is explicitly implemented in `SeverityEngine._generate_mixture_first_component`.

---

## Portfolio aggregation semantics

Implemented in `crml_engine/src/crml_engine/runtime.py`.

Supported `portfolio.semantics.method` values (execution-time semantics):

- `sum`
- `max`
- `mixture`
- `choose_one`

---

## Multi-currency

The engine supports:

- Per-event severity currencies in scenarios (e.g., `USD`, `EUR`).
- Converting results into an output currency via an FX config.

See: [Multi-Currency Support](../../Multi-Currency-Support.md)
