# Engine capabilities: Portfolio execution

This page documents reference-engine behavior when executing portfolios.

---

## Execution flow (reference engine)

1. **Load + validate** the portfolio and referenced artifacts (`crml_lang`).
2. **Plan** an execution plan (bind scenarios to assets, resolve controls).
3. **Simulate** each planned scenario for `n_runs`.
4. **Aggregate** scenario losses into a portfolio loss sample using `portfolio.semantics.method`.

Implementation pointers:

- Planning: `crml_engine/src/crml_engine/pipeline/portfolio_planner.py`
- Runtime execution: `crml_engine/src/crml_engine/runtime.py`

---

## Exposure scaling

Portfolio scenario bindings determine an exposure cardinality $E$ which the engine uses when the scenario’s frequency basis is `per_asset_unit_per_year`.

The *portable* definition of $E$ and basis semantics is in [CRML Specification (Overview)](../../Reference/CRML-Specification.md).

---

## Aggregation semantics

The reference runtime aggregates the simulated per-run annual loss arrays using one of:

- `sum`: elementwise sum
- `max`: elementwise maximum
- `mixture`: choose a scenario per run using weights (if provided)
- `choose_one`: same selection mechanism as `mixture` (engine-defined distinction is currently minimal)

These are implemented by `_aggregate_portfolio_losses`.

---

## Dependency: control-state copula

The portfolio schema allows an optional `portfolio.dependency.copula` section.

In the **reference engine**, this dependency is used to correlate *binary control up/down state* across controls.

### Supported target format

Targets MUST be strings of the form:

- `control:<id>:state`

This is validated in the portfolio planner before execution.

### Correlation matrix sources

Two ways to define the correlation matrix:

1) Provide an explicit matrix:

```yaml
portfolio:
  dependency:
    copula:
      type: gaussian
      targets:
        - control:cap:edr:state
        - control:cap:mfa:state
      matrix:
        - [1.0, 0.5]
        - [0.5, 1.0]
```

2) Provide Toeplitz structure (reference engine supports `structure: toeplitz`):

```yaml
portfolio:
  dependency:
    copula:
      type: gaussian
      structure: toeplitz
      rho: 0.65
      targets:
        - control:cap:edr:state
        - control:cap:mfa:state
```

The planner expands this into an explicit matrix in the execution plan.

---

## Bundles

If you execute a `crml_portfolio_bundle: "1.0"`, the engine prefers inlined scenario documents from the bundle (to avoid filesystem dependence).
