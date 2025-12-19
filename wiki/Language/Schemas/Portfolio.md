# Portfolio Schema (`crml_portfolio: "1.0"`)

This page documents the CRML **Portfolio** document shape and how to use it.

- JSON Schema: `crml_lang/src/crml_lang/schemas/crml-portfolio-schema.json`
- Pydantic model: `crml_lang/src/crml_lang/models/portfolio_model.py` (`CRPortfolio`)

---

## What a portfolio is

A portfolio provides **exposure** (assets and cardinalities) and binds one or more scenarios to that exposure.

Portfolios may also reference control packs (catalogs, assessments, mappings) so engines/tools can apply control posture and do cross-framework resolution.

---

## Top-level structure

```yaml
crml_portfolio: "1.0"
meta: { ... }
portfolio: { ... }
```

---

## Minimal example

```yaml
crml_portfolio: "1.0"
meta:
  name: "Example portfolio"
portfolio:
  semantics:
    method: sum
    constraints:
      require_paths_exist: true
      validate_scenarios: true
  assets:
    - name: employees
      cardinality: 250
    - name: endpoints
      cardinality: 450
  scenarios:
    - id: phishing
      path: ../scenarios/scenario-phishing.yaml
      binding:
        applies_to_assets: [employees]
```

See also: `examples/portfolios/portfolio.yaml`.

---

## `portfolio.semantics`

```yaml
semantics:
  method: sum | mixture | choose_one | max
  constraints:
    require_paths_exist: <bool>
    validate_scenarios: <bool>
    validate_relevance: <bool>
```

Notes:

- `method` determines how scenario losses are aggregated (engine uses this as guidance).
- `constraints` influence validation behavior in tools:
  - `require_paths_exist`: if true, referenced file paths must exist during validation
  - `validate_scenarios`: if true, referenced scenarios are schema-validated during portfolio validation
  - `validate_relevance`: enables extra checks using `meta` context

---

## `portfolio.assets`

Each asset is an exposure bucket.

```yaml
assets:
  - name: endpoints
    cardinality: 450
    tags: ["it", "endpoint"]
```

Notes:

- `name` must be unique in the portfolio.
- `cardinality` is parsed leniently (some numberish inputs are accepted).

---

## `portfolio.scenarios` (references + bindings)

Each scenario reference includes:

- `id`: unique id within the portfolio
- `path`: file path to the scenario document
- `binding.applies_to_assets` (optional): list of asset names defining the exposure set
- `weight` (optional): used by some aggregation methods

Example:

```yaml
scenarios:
  - id: phishing
    path: ../scenarios/scenario-phishing.yaml
    binding:
      applies_to_assets: [employees]
```

Binding semantics are standardized in `wiki/Reference/CRML-Specification.md` (Exposure scaling section).

---

## `portfolio.controls` (optional inventory)

Portfolios MAY define controls directly:

```yaml
controls:
  - id: org:iam.mfa
    implementation_effectiveness: 0.7
    coverage: { value: 0.9, basis: employees }
    reliability: 0.99
    affects: frequency
```

Many workflows instead rely on assessment packs for posture values.

---

## Referencing control packs

Portfolios can reference external documents by path:

- `control_catalogs`: list of control catalog files
- `assessments`: list of assessment files
- `control_relationships`: list of control relationship pack files

Important semantic rule:

- If `portfolio.assessments` is used, `portfolio.control_catalogs` must also be provided (so assessment ids can be interpreted consistently).

---

## Scenario-to-scenario relationships (optional)

`portfolio.relationships` supports:

- correlation edges (`type: correlation`, `between: [a, b]`, `value: -1..1`)
- conditional edges (`type: conditional`, `given: a`, `then: b`, `probability: 0..1`)

---

## Dependency modeling (optional)

Portfolios can specify an engine-independent copula structure:

```yaml
dependency:
  copula:
    type: gaussian
    targets:
      - "control:org:iam.mfa:state"
      - "control:org:edr:state"
    structure: toeplitz
    rho: 0.35
```

---

## Validation

Python:

```python
from crml_lang import validate_portfolio
report = validate_portfolio("examples/portfolios/portfolio.yaml", source_kind="path")
assert report.ok
```

For exact constraints, consult `crml_lang/src/crml_lang/schemas/crml-portfolio-schema.json`.
