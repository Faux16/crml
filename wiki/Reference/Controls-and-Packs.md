# Controls & Packs (Reference)

This page defines the **normative** semantics for controls in current CRML scenario/portfolio documents and how control-related “packs” interact.

> Note: The CRML 1.1 spec pages describe an older, runtime-centric “layers” model. This page documents the newer packs-based approach.

---

## Concepts

### Control ID

A control is identified by a stable, portable **Control ID**.

- Format: `namespace:key`
- Example: `cis:4.1`, `iso27001:a.8.12`, `org:iam.mfa`
- Purpose: a short identifier that can be referenced from scenarios, portfolios, catalogs, and assessments.

Control IDs are **identifiers only**. Avoid embedding copyrighted control text inside CRML artifacts.

### Control Catalog Pack

A **Control Catalog Pack** declares the universe of control IDs (and optional metadata) that a team agrees to use.

- Document header: `crml_control_catalog: "1.0"`
- Core content: `catalog.controls[]` with at least `id`

Catalogs are intended for:

- Validation (“is this ID known?”)
- Tooling/UI mapping (“show title/url/tags for an ID”)

Catalogs do **not** provide organization-specific posture values.

### Control Assessment Pack

A **Control Assessment Pack** records organization posture for a set of controls.

- Document header: `crml_control_assessment: "1.0"`
- Core content: `assessments[]`

Each assessment is scoped to a control ID and includes:

- `implementation_effectiveness`: $[0,1]$
- Optional `coverage` object
- Optional `reliability`: $[0,1]$ (control “up/down” probability)
- Optional `affects`: `frequency`, `severity`, or `both`

Assessments are the preferred place to store org-wide posture.

### Portfolio Control Inventory

A **Portfolio** is the executable context for scenarios.

- Document header: `crml_portfolio: "1.0"`
- Control inventory: `controls[]`

In portfolio planning/validation, control posture can come from either:

- A portfolio’s inline `controls[]` inventory, and/or
- Control Assessment Packs referenced by the portfolio.

### Scenario Control References

A **Scenario** may reference controls in a lightweight way, so scenarios remain portable.

- Document header: `crml_scenario: "1.0"`
- Controls live under `scenario.controls[]`

A scenario control reference can be:

- A string Control ID: `"org:iam.mfa"`
- An object: `{ id, implementation_effectiveness?, coverage?, potency?, notes? }`

The object form is for scenario-specific assumptions.

---

## Coverage

Coverage is represented as a structured object:

```yaml
coverage:
  value: 0.8
  basis: endpoints
  notes: "Covers most endpoints, not OT"
```

Normative rules:

- `coverage.value` MUST be in $[0,1]$.
- `coverage.basis` MUST be an allowed enum value.
- Coverage is interpreted as a **multiplier-like** concept (how broadly the control applies), distinct from `implementation_effectiveness` (how well the control works where applied).

---

## Effective Control Parameters (Merge)

When multiple sources provide parameters for the same control ID, tools MUST derive “effective” parameters using these rules:

- Portfolio inventory values (if present) SHOULD take precedence over assessment pack values.
- Scenario control objects are interpreted as **scenario-level applicability factors** that multiply the portfolio/assessment values.

Normative details:

- If a scenario reference is a string ID (no object fields), it applies the portfolio/assessment values as-is.
- If a scenario reference is an object, `implementation_effectiveness`, `coverage`, and `potency` are interpreted as multiplicative factors in $[0,1]$.
- If a scenario references a control id and no portfolio inventory or assessment provides posture values, portfolio planning/validation MUST fail.

> Implementation note: today the validator enforces the “scenario controls must exist in portfolio.controls” rule when validating a portfolio that loads scenarios. Portfolio-to-pack auto-loading/merging may be implemented by tooling/runtime.

### Example: same control appears in multiple sources

Assume control `org:iam.mfa` is present in an assessment pack and referenced by a scenario.

Assessment pack (org-wide posture):

```yaml
crml_control_assessment: "1.0"
meta: {name: "Org assessment"}
assessment:
  framework: "Org"
  assessments:
    - id: "org:iam.mfa"
      implementation_effectiveness: 0.7
      reliability: 0.99
      affects: frequency
      coverage: {value: 0.9, basis: employees}
```

Portfolio control inventory (optional executable overrides):

```yaml
crml_portfolio: "1.0"
meta: {name: "Org portfolio"}
portfolio:
  semantics: {method: sum}
  controls:
    - id: "org:iam.mfa"
      implementation_effectiveness: 0.5
```

Scenario-specific assumption (highest precedence):

```yaml
crml_scenario: "1.0"
meta: {name: "Phishing"}
scenario:
  controls:
    - id: "org:iam.mfa"
      implementation_effectiveness: 0.6  # scenario-level factor
      potency: 0.5  # threat-specific potency factor
      notes: "Assume limited MFA enforcement for this scenario"
```

Effective `implementation_effectiveness` for this scenario is `0.5 × 0.6 × 0.5 = 0.15` (portfolio overrides assessment, then scenario scales it, then potency applies).

### Example: field-by-field override

If the scenario only overrides coverage, the assessment’s implementation effectiveness remains in effect.

```yaml
scenario:
  controls:
    - id: "org:iam.mfa"
      coverage: {value: 0.6, basis: employees}
```

Effective `implementation_effectiveness` comes from portfolio (if present) else assessment; effective `coverage` is multiplied by the scenario factor.

---

## Validation Rules

### Schema vs semantic validation

- JSON Schema validates document structure.
- Semantic validation enforces cross-field and cross-document rules.

### Catalog validation

A Control Catalog Pack MUST be rejected if:

- Any control ID is duplicated within the same catalog.

### Assessment validation

A Control Assessment Pack MUST be rejected if:

- Any assessment ID is duplicated within the same assessment pack.

If catalogs are supplied alongside validation, an assessment pack MUST also be rejected if:

- Any assessment control ID does not exist in the supplied catalogs.

### Portfolio cross-document validation

When validating a portfolio that references scenario documents:

- Every control referenced by each scenario MUST have posture values available (via `portfolio.controls[]` and/or referenced assessment packs).

---

## Minimal Examples

### Catalog pack

```yaml
crml_control_catalog: "1.0"
catalog:
  name: "Org control IDs"
  controls:
    - id: "org:iam.mfa"
    - id: "org:edr"
```

### Assessment pack

```yaml
crml_control_assessment: "1.0"
meta: {name: "Org assessment"}
assessment:
  framework: "Org"
  assessments:
    - id: "org:iam.mfa"
      implementation_effectiveness: 0.7
      reliability: 0.99
      affects: frequency
      coverage:
        value: 0.9
        basis: employees
```

### Scenario control references

```yaml
crml_scenario: "1.0"
meta: {name: "Phishing -> account takeover"}
scenario:
  frequency: {basis: per_organization_per_year, model: poisson, parameters: {lambda: 0.8}}
  severity: {model: lognormal, parameters: {mu: 10, sigma: 1.2, currency: USD}}
  controls:
    - "org:iam.mfa"
    - id: "org:edr"
      implementation_effectiveness: 0.5
      notes: "Assume partial tuning against this TTP"
```
