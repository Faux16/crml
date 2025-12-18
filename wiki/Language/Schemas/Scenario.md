# Scenario Schema (`crml_scenario: "1.0"`)

This page documents the CRML **Scenario** document shape and provides two authoring workflows:

- **Profile A (Threat report baseline):** fast authoring from threat reports and news.
- **Profile B (Internal calibration):** calibrate/validate using internal incident and loss data.

- JSON Schema: `crml_lang/src/crml_lang/schemas/crml-scenario-schema.json`
- Pydantic model: `crml_lang/src/crml_lang/models/scenario_model.py` (`CRScenarioSchema`)

---

## What a scenario is

A scenario is a portable **threat/risk model** made of:

- `scenario.frequency`: how often the threat event occurs
- `scenario.severity`: how large the loss is per event

A scenario is **not executable on its own**: execution happens in a **portfolio**, which provides exposure (assets/cardinalities) and binds scenarios to that exposure.

Practical interpretation:

- You can author a scenario from external reporting (baseline).
- You can later refine it with internal evidence and calibrate the parameters.

---

## Top-level structure

Required:

```yaml
crml_scenario: "1.0"
meta: { ... }
scenario: { ... }
```

Optional:

- `evidence:` citations + lightweight observed metrics (recommended for threat-report authoring)
- `data:` internal data integration hook (recommended for calibration tooling)

---

## Profile A: Threat report baseline (recommended starting point)

Use this profile when your inputs are mostly from **threat reports/news**:

- narrative + targeting (industry/region)
- observed counts over a time window (sometimes)
- a typical loss number or range (sometimes)
- recommended mitigations (almost always)

### What to fill

1) Put provenance into `evidence.sources` (URLs, vendor report names, dates).

2) Set frequency as a baseline:

- Prefer `basis: per_organization_per_year` for externally sourced intelligence.
- `frequency.model` is optional; if omitted it defaults to `poisson`.
- Set `frequency.parameters.lambda` to a reasonable baseline per year.

3) Set severity minimally:

- Prefer `severity.parameters.median` for human authoring.
- Choose a reasonable `sigma` if you don’t have internal data yet.

4) List recommended relevant controls in `scenario.controls`.

### Example (baseline from reporting)

```yaml
crml_scenario: "1.0"
meta:
  name: "Phishing -> account takeover"
  description: "Baseline scenario authored from external reporting; calibrate with internal incidents when available."
  tags: ["threat-report", "phishing", "ato"]
  industries: ["cross-industry"]
  attck: ["attck:T1566"]

evidence:
  sources:
    - title: "Example Threat Report 2025"
      publisher: "Vendor X"
      url: "https://example.com/report"
      published_at: "2025-09-01"
      retrieved_at: "2025-12-18"
      notes: "Used for incident frequency and typical loss guidance."
  observed:
    window: { start: "2024-01-01", end: "2024-12-31" }
    incident_count: 120
    org_count: 500
    currency: USD
    loss_median: 20000
    loss_p90: 150000

scenario:
  controls:
    - id: "org:iam.mfa"
    - id: "org:mail.phishing_training"
  frequency:
    basis: per_organization_per_year
    parameters:
      lambda: 0.8
  severity:
    model: lognormal
    parameters:
      currency: USD
      median: 20000
      sigma: 1.2
```

Implementation note:

- A tool can optionally derive $\lambda$ from evidence like:
  $$\lambda \approx \frac{\text{incident\_count}}{\text{org\_count} \cdot \text{years}}$$
  and then write it back into `scenario.frequency.parameters.lambda`.

---

## Profile B: Internal calibration (incident and loss data)

Use this profile when you have internal data sources (incident logs, ticket exports, loss accounting) and you want to:

- validate that your baseline model roughly matches reality
- calibrate $\lambda$ and severity parameters

### What to fill

1) Keep `evidence` for provenance (optional but recommended).

2) Describe internal datasets in `data.sources` and map fields with `data.feature_mapping`.

3) Calibrate severity using per-incident losses:

- populate `scenario.severity.parameters.single_losses` (portable, no engine-specific feature naming)

4) Calibrate frequency:

- update `scenario.frequency.parameters.lambda`

### Example (calibration-oriented)

```yaml
crml_scenario: "1.0"
meta:
  name: "Phishing -> account takeover (calibrated)"
  tags: ["internal-calibrated", "phishing", "ato"]

data:
  sources:
    org_incidents_2022_2025:
      type: incident_log_csv
      data_schema:
        occurred_at: datetime
        loss_usd: money
        scenario_label: string
  feature_mapping:
    incident_timestamp: occurred_at
    incident_loss_amount: loss_usd

scenario:
  controls:
    - id: "org:iam.mfa"
  frequency:
    basis: per_organization_per_year
    model: poisson
    parameters:
      lambda: 1.3
  severity:
    model: lognormal
    parameters:
      currency: USD
      single_losses: [12000, 5000, 90000, 18000, 24000]
```

---

## `evidence` (citations + lightweight observed metrics)

The optional top-level `evidence` section is designed to match what **threat reports/news** provide.

Use it to store:

- citations (`evidence.sources`)
- coarse observed counts and summary loss statistics (`evidence.observed`)

Tools can use `evidence` to help compute model parameters, but the executable model remains `scenario.frequency` + `scenario.severity`.

Important constraints:

- `evidence` is portable metadata; it should not contain secrets.
- Date/timestamps are stored as ISO 8601 strings.

---

## `data` (data sources and feature mapping)

The optional top-level `data` section is an **integration hook** for tools and engines.

It is designed for workflows where an organization wants to attach internal datasets that can be used to **calibrate** or **validate** the scenario.

Important constraints:

- The CRML language validates the *shape* of `data`, but does not standardize source `type` strings or feature names.
- Engines and UIs SHOULD treat `data` as optional and ignore unknown feature names.
- Do not put secrets (API keys, credentials) into CRML documents.

### `data.sources`

`data.sources` is an optional map of named sources. Each source has:

- `type`: engine/UI-defined identifier (e.g. `csv`, `parquet`, `snowflake`, `servicenow_export`, `siem_incidents`)
- `data_schema` (optional): a free-form mapping describing fields available in that source

Notes:

- `sources` deliberately does not include a portable `path`/`uri` field. Tools that need locations should handle that out-of-band to keep CRML portable.

### `data.feature_mapping`

`data.feature_mapping` maps **engine/tool feature names** to source fields.

Recommended convention:

- Feature names should be stable within a tool/engine.
- If multiple sources are used, tools can adopt a qualified convention (e.g. `source_name.field`) in their own feature naming.

---

## `scenario.frequency`

Structure:

```yaml
frequency:
  basis: per_organization_per_year | per_asset_unit_per_year
  model: <engine-defined>           # optional, defaults to poisson
  parameters: { ... }
```

Notes:

- `basis` controls exposure scaling in portfolios. See “Exposure scaling and frequency basis” in `wiki/Reference/CRML-Specification.md`.
- `model` is engine-defined; if omitted it defaults to `poisson`.
- `parameters` is model-specific. Common parameter names:
  - `lambda` (serialized as `lambda`, stored as `lambda_` internally)
  - `p`, `alpha_base`, `beta_base`, `r`, …

Implementation guidance (converting report counts to $\lambda$):

- If a report gives $N$ incidents across $Y$ years for a single organization:
  $$\lambda \approx \frac{N}{Y}$$
- If a report gives $N$ incidents across $Y$ years across $O$ organizations:
  $$\lambda_{per\_org} \approx \frac{N}{O \cdot Y}$$

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

- `model` is engine-defined.
- For authoring from reporting, prefer `median` and set a reasonable `sigma` until calibrated.
- For calibration, prefer `single_losses` (per-incident samples).

### Calibration-friendly inputs (`single_losses`)

Populate `scenario.severity.parameters.single_losses` with per-incident loss samples.

- Values should be positive and represent one value per event (not annual totals).
- Tools SHOULD validate that there are at least 2 values.

---

## `scenario.controls` (threat-centric relevant controls)

`scenario.controls` is an optional, threat-centric declaration of controls that can mitigate this scenario.

Each entry can be either:

- a canonical control id string (e.g. `org:iam.mfa`), or
- an object with scenario-scoped overrides:

```yaml
- id: "org:iam.mfa"
  effectiveness_against_threat: 0.8  # optional
  notes: "..."                       # optional
```

Semantics (recommended):

- `effectiveness_against_threat` is a threat-specific factor.
- Organization-specific posture belongs in portfolio inventory and/or assessments.

---

## Validation

Python:

```python
from crml_lang import validate_scenario

report = validate_scenario("examples/scenarios/scenario-phishing.yaml", source_kind="path")
assert report.ok
```

For field-by-field constraints, consult `crml_lang/src/crml_lang/schemas/crml-scenario-schema.json`.
