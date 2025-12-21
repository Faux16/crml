# Understanding parameters

This guide gives practical intuition for common CRML parameters.

For the portable semantics and document shapes, see:

- [CRML Specification (Overview)](../Reference/CRML-Specification.md)
- [Scenario schema](../Language/Schemas/Scenario.md)

---

## Frequency (`lambda`)

For a Poisson frequency model, `lambda` is the expected number of events per year **in the configured basis**.

- If basis is `per_organization_per_year`, `lambda` is the org-wide expected annual event count.
- If basis is `per_asset_unit_per_year`, the effective annual rate is scaled by bound exposure $E$.

See: [Runtime (Frequency)](../Concepts/Runtime-Frequency.md)

---

## Severity (lognormal)

Common parameters:

- `median`: median single-event loss
- `sigma`: log-space spread
- `currency`: currency code

See: [Runtime (Severity)](../Concepts/Runtime-Severity.md)

---

## Simulation runs

Percentile estimates (VaR) stabilize more slowly than means.

- Use smaller `--runs` while iterating.
- Increase runs for reporting.
