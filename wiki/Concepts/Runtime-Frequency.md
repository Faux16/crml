# Runtime (Frequency)

This page explains common frequency models used in CRML scenarios.

CRML frequency is expressed as a **rate model** plus a **basis**:

- `scenario.frequency.model`: a model identifier (engine-defined support)
- `scenario.frequency.basis`: portable semantic meaning of the rate unit

See: [CRML Specification (Overview)](../Reference/CRML-Specification.md)

---

## Basis semantics (portable)

Two basis values are standardized by the language:

- `per_organization_per_year`: the scenario’s frequency already represents the total org-wide annual rate.
- `per_asset_unit_per_year`: the scenario’s frequency represents a per-unit annual rate and MUST be scaled by bound exposure $E$.

For the normative definition of $E$ (how portfolios bind scenarios to assets), see [Exposure scaling and frequency basis](../Reference/CRML-Specification.md#exposure-scaling-and-frequency-basis-normative).

---

## Common models

### Poisson

A Poisson process is often used for independent event counts.

If the annual rate is $\lambda$, then the event count $N$ in a year is:

$$
N \sim \text{Poisson}(\lambda)
$$

For `per_asset_unit_per_year`, the effective annual rate becomes:

$$
\lambda_{\text{total}} = \lambda \cdot E
$$

### Gamma–Poisson (negative binomial)

A common way to model over-dispersion is to treat the Poisson rate as random:

$$
\lambda \sim \text{Gamma}(k, \theta), \quad N \mid \lambda \sim \text{Poisson}(\lambda)
$$

The resulting marginal distribution for $N$ is negative binomial-like (engine parameterization may vary).

### Hierarchical Gamma–Poisson

A hierarchical extension can model uncertainty in rate parameters across similar organizations or units. Details are engine-defined.

---

## Reference engine status

Implemented frequency models in the reference engine are listed here:

- [Engine capabilities: Supported models](../Engine/Capabilities/Supported-Models.md)
