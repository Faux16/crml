# CRML Specification

This page is the entry point for the CRML language contracts (schemas + minimal semantics) and how they relate to execution engines.

- Language overview: [Architecture-Language](../Concepts/Architecture-Language)
- Engine overview: [Architecture-Engine](../Concepts/Architecture-Engine)
- JSON Schemas: [CRML-Schema](CRML-Schema)
- Practical workflow: [Quickstart](../Quickstart)

CRML is designed so that:

- The **language** (`crml_lang`) defines document shapes and a small set of portable semantics.
- **Engines** (including the reference engine `crml_engine`) decide how to fit/infer/execute models and which algorithms and outputs they support.

Normative keywords on this page are interpreted as in RFC 2119: **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, **MAY**.

---

## Language vs engine responsibilities

**Language-defined (portable)**

- Document discriminators and top-level shapes (e.g. `crml_scenario: "1.0"`).
- Field meaning at the “common denominator” level (e.g. frequency basis, severity parameter intent).
- Cross-document linking rules (e.g. a portfolio references scenarios and binds them to assets).
- Minimal semantics for exposure scaling (see below).

**Engine-defined (implementation-specific)**

- Which `scenario.frequency.model` and `scenario.severity.model` identifiers are supported.
- Fitting/inference workflows (e.g. MCMC/VI), diagnostics, and report formats.
- Runtime options (sample counts, seeds, performance knobs).
- Execution-time configuration documents (e.g. FX config) and engine-specific extensions.

---

## Current CRML document types

CRML is **document-oriented**. Rather than a single “model file”, you typically manage multiple documents (often via CRML Studio or a similar tool).

### Scenario document (`crml_scenario: "1.0"`)

A scenario describes one risk model (frequency + severity, optional controls) without asserting portfolio exposure.

Minimal structure:

```yaml
crml_scenario: "1.0"
meta:
  name: "example"
  version: "1.0"
scenario:
  frequency:
    basis: per_organization_per_year
    model: poisson
    parameters:
      lambda: 0.1
  severity:
    model: lognormal
    parameters:
      median: 22000
      currency: USD
      sigma: 1.0
```

Notes:

- `scenario.frequency.basis` expresses the unit basis of the event rate (see “Exposure scaling” below).
- `scenario.severity.parameters` is required (may be `{}` for parameterless models).

### Portfolio document (`crml_portfolio: "1.0"`)

A portfolio defines exposure (assets and cardinalities) and binds one or more scenarios to some or all assets.

Minimal structure:

```yaml
crml_portfolio: "1.0"
meta:
  name: "example-portfolio"
portfolio:
  assets:
    - name: endpoints
      cardinality: 500
    - name: employees
      cardinality: 100
  scenarios:
    - scenario: "scenarios/phishing.yaml"
      binding:
        applies_to_assets: [employees]
```

Notes:

- `portfolio.scenarios[].binding.applies_to_assets` MAY be omitted/null, in which case it is interpreted as “all portfolio assets”.
- If `applies_to_assets` is an empty list, it binds to no assets (total exposure $E=0$); engines SHOULD treat this as a configuration error for per-asset frequency basis.

### Control packs (`crml_control_catalog`, `crml_assessment`, `crml_control_relationships`)

Control catalogs, assessments, and control relationships are separate documents that can be referenced from portfolios.

- If a portfolio references `assessments`, it MUST also reference the corresponding `control_catalogs` (so the assessment IDs can be interpreted).

Control relationships packs (`crml_control_relationships: "1.0"`) provide portable **control-to-control mappings** (grouped 1→N by source) with quantitative overlap metadata.

- A portfolio MAY reference `control_relationships` to enable tools/engines to resolve scenario control ids to implemented portfolio controls (especially when different frameworks or id namespaces are involved).

### Portfolio bundles and simulation results

CRML also defines stable “envelope” documents for interoperability:

- `crml_portfolio_bundle: "1.0"` (a bundle of portfolio + referenced artifacts)
- `crml_simulation_result: "1.0"` (a results document)

---

## Exposure scaling and frequency basis (normative)

This section standardizes the minimal semantics needed for consistent portfolio scaling across engines.

### Definitions

- Each portfolio asset has a non-negative integer `cardinality` (number of exposure units).
- For a portfolio scenario reference, define the bound asset set $A$:
  - If `binding.applies_to_assets` is omitted or null: $A$ is all portfolio assets.
  - If `binding.applies_to_assets` is provided: $A$ is exactly that list.
- Define total bound exposure $E$ as:

$$
E = \sum_{a \in A} \mathrm{cardinality}(a)
$$

### Basis semantics

- If `scenario.frequency.basis` is `per_organization_per_year`:
  - Engines MUST treat the frequency model as already expressing the total organization-wide annual rate.
  - Asset bindings MUST NOT change the expected annual event count (i.e. the effective exposure multiplier is 1).

- If `scenario.frequency.basis` is `per_asset_unit_per_year`:
  - Engines MUST scale the expected annual event count linearly with $E$.
  - For example, for a Poisson model with per-unit rate $\lambda$:

$$
\lambda_{\mathrm{total}} = \lambda \cdot E
$$

### Validation guidance

- If `per_asset_unit_per_year` and $E=0$, tools SHOULD emit a validation error or warning (no exposure bound).
- If `per_organization_per_year` and `applies_to_assets` is provided, tools SHOULD warn that the binding does not affect frequency (but may still affect control coverage or reporting).

Notes:

- These checks are implementable at the **language/tooling** layer because they depend only on (a) the portfolio assets/binding and (b) the referenced scenario’s `frequency.basis`.
- The reference implementation in this repository emits these as **semantic warnings** during portfolio validation via `crml_lang.validate_portfolio(...)`.
- Because the checks require reading the referenced scenario document to know `frequency.basis`, they are emitted when portfolio validation is configured to load scenarios (e.g. `portfolio.semantics.constraints.validate_scenarios: true`) and the scenario file can be loaded.

Example (Python):

```python
from crml_lang import validate_portfolio

report = validate_portfolio("examples/portfolios/portfolio.yaml", source_kind="path")
for w in report.warnings:
  print(w.path, w.message)
```
