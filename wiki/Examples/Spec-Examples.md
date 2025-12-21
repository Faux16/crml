# Specification Examples

This page highlights small, spec-level examples using the **current CRML document contracts**.

In this repository:

- Scenario documents use `crml_scenario: "1.0"`.
- Portfolio documents use `crml_portfolio: "1.0"`.
- FX config is an execution-time config document (`crml_fx_config: "1.0"`).

For full, runnable examples, see [Full Examples](Full-Examples).

## Scenario document header

```yaml
crml_scenario: "1.0"
meta:
  name: "example"
  version: "2025.1"
  description: "Short description."
scenario:
  frequency:
    basis: per_organization_per_year
    model: poisson
    parameters:
      lambda: 0.2
  severity:
    model: lognormal
    parameters:
      median: "100 000"
      currency: USD
      sigma: 1.2
```

## Median-based parameterization (recommended)

Using `median` is often more auditable than `mu`:

```yaml
severity:
  model: lognormal
  parameters:
    median: "250 000"
    currency: EUR
    sigma: 1.2
```

## Multi-currency inputs + external FX config

CRML scenarios can tag monetary inputs with a currency. FX rates are not embedded into the risk model; they are supplied at execution time.

FX config document:

```yaml
crml_fx_config: "1.0"
base_currency: USD
output_currency: EUR
rates:
  USD: 1.0
  EUR: 1.08
```

## Portfolio document header

```yaml
crml_portfolio: "1.0"
meta:
  name: "example-portfolio"
portfolio:
  semantics:
    method: sum
    constraints:
      validate_scenarios: true
  scenarios:
    - id: s1
      path: ./scenario.yaml
```

## Limitations and portability notes

- Model identifiers (e.g., `poisson`, `mixture`) are engine-defined.
- Component structures (e.g., `severity.components`) are engine-defined.
- Any inference pipelines, exports, or runtime options belong in engine/tool configuration, not in the CRML documents.
