# Scenario Schema (`crml_scenario: "1.0"`)

This page documents the CRML **Scenario** document shape and how to use it.

- JSON Schema: `crml_lang/src/crml_lang/schemas/crml-scenario-schema.json`
- Pydantic model: `crml_lang/src/crml_lang/models/crml_model.py` (`CRScenarioSchema`)

---

## What a scenario is

A scenario is a **threat/risk model** (frequency + severity) that is portable and can be validated on its own.

A scenario is not directly executable by itself: execution happens in a **portfolio**, which provides exposure (assets/cardinalities) and binds scenarios to that exposure.

---

## Top-level structure

Required:

```yaml
crml_scenario: "1.0"
meta: { ... }
scenario: { ... }
```

Optional:

- `data:` (data sources and feature mapping for tools/engines)

---

## Minimal example

```yaml
crml_scenario: "1.0"
meta:
  name: "Phishing -> account takeover"
scenario:
  controls:
    - id: "org:iam.mfa"
      potency: 0.85
  frequency:
    basis: per_organization_per_year
    model: poisson
    parameters:
      lambda: 0.8
  severity:
    model: lognormal
    parameters:
      mu: 10
      sigma: 1.2
      currency: USD
```

See also: `examples/scenarios/scenario-phishing.yaml`.

---

## `meta` (document metadata)

`meta` is shared across CRML document types.

Common fields:

- `name` (required): human-friendly name
- `version`, `description`, `author`, `organization` (optional)
- `tags`, `industries`, `company_sizes`, `regulatory_frameworks` (optional)
- `locale` (optional object): free-form locale/region metadata

---

## `scenario.frequency`

Structure:

```yaml
frequency:
  basis: per_organization_per_year | per_asset_unit_per_year
  model: <engine-defined>
  parameters: { ... }
```

Notes:

- `basis` controls exposure scaling in portfolios. See the normative section “Exposure scaling and frequency basis” in `wiki/Reference/CRML-Specification.md`.
- `model` is **engine-defined** (the language validates it as a string).
- `parameters` is model-specific. The language provides some standardized parameter names used by common models:
  - `lambda` (serialized as `lambda`, stored as `lambda_` internally)
  - `p`, `alpha_base`, `beta_base`, `r`, …

Number parsing:

- Some numeric parameters accept “numberish” inputs (e.g. strings like `"700 000"`). Tools should prefer plain numbers, but the language is permissive for human authing.

---

## `scenario.severity`

Structure:

```yaml
severity:
  model: <engine-defined>
  parameters: { ... }
  components: [ ... ]  # optional
```

Notes:

- `model` is **engine-defined**.
- `parameters` supports several common distribution parameter styles:
  - Human-friendly: `median` (often preferred)
  - Distribution-specific: `mu`, `sigma`, `shape`, `scale`, etc.
  - `currency` is optional and is primarily a hint to engines/tools
- `components` is an optional engine/tool-defined breakdown.

---

## `scenario.controls` (threat-centric relevant controls)

`scenario.controls` is optional and expresses the set of controls that can mitigate this scenario.

Each entry can be either:

- a canonical control id string (e.g. `org:iam.mfa`), or
- an object with scenario-scoped overrides:

```yaml
- id: "org:iam.mfa"
  implementation_effectiveness: 0.8  # optional
  potency: 0.85                      # optional
  coverage: { value: 0.9, basis: employees }  # optional
  notes: "..."                       # optional
```

Semantics (recommended):

- `implementation_effectiveness` is an optional scenario-scoped override.
- `potency` represents how strong the control is against this specific scenario.
- `coverage` represents breadth of application.

Engines combine scenario-scoped values with portfolio/assessment posture during planning.

---

## Validation

CLI / tooling validation routes through `crml_lang`.

Python:

```python
from crml_lang import validate_scenario
report = validate_scenario("examples/scenarios/scenario-phishing.yaml", source_kind="path")
assert report.ok
```

For field-by-field constraints, consult `crml_lang/src/crml_lang/schemas/crml-scenario-schema.json`.
