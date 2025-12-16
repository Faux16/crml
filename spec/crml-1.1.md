# CRML 1.1 — Cyber Risk Modeling Language

**Status:** Draft
**Spec Version:** 1.1
**Scope:** This document defines the CRML 1.1 standard. CRML 1.1 is defined as the CRML 1.0 core, plus the additions/clarifications enumerated in “Changes from 1.0”.

CRML (Cyber Risk Modeling Language) is a declarative, implementation-agnostic language for defining cyber risk models and their execution configuration. A CRML document is written in YAML or JSON and is designed to be consumed by different execution engines (e.g., FAIR-style Monte Carlo, QBER-style Bayesian engines).

Normative keywords in this document are interpreted as described in RFC 2119: **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, **MAY**.

## 0. Terminology and How Things Fit Together

This section is explanatory (non-normative) and is intended to clarify the roles involved in a typical CRML workflow.

### 0.1 Terms

- **CRML (the language)**: The standard defined by this specification. It defines the allowed document structure and the meaning of fields like `model.frequency`, `model.severity`, `data.sources`, and `data.feature_mapping`.

- **CRML document (or “model file”)**: A YAML instance that declares `crml: "1.1"` and contains a risk model definition. This file is intended to be portable across environments.

- **Consumer**: Any software that reads a CRML document. A consumer may validate it, render it for humans, transform it, or execute it.

- **Engine**: A consumer that can execute the model semantics (e.g., simulate losses, perform inference, compute metrics). In practice, engines usually include:
  - a **parser/validator** (to read CRML)
  - a **runtime** (to execute distributions and pipelines)
  - a **data binding layer** (to supply real data for `data.sources`)

- **Data binding (or “source binding”)**: The execution-time step where a consumer/engine provides concrete data for each declared `data.sources.<source_name>` so that `data.feature_mapping` can be resolved into actual vectors/columns.

- **Binding configuration**: A separate configuration (CLI flags, config file, application code) that tells an engine *where* the real data comes from (file path, DB table, API endpoint, etc.) and *how* to authenticate.

### 0.2 Why CRML models do not contain endpoints or credentials

CRML documents intentionally avoid embedding connectivity details (API endpoints, usernames, tokens) because:

- **Security**: models are commonly stored in Git, attached to tickets, or shared; embedding secrets is risky.
- **Portability**: the same model should run in dev/staging/prod and across organizations without editing URLs/tenants.
- **Auditability**: risk assumptions (frequency/severity) are reviewed differently and change at a different cadence than credentials and infrastructure.

### 0.3 Typical end-to-end flow

1. **Authoring**: a model author writes a CRML document describing:
  - expected data shapes (`data.sources.schema`)
  - which fields the model uses (`data.feature_mapping`)
  - the risk math (`model.*`)

2. **Binding**: at execution time, the engine is given (or already has) a binding configuration that maps each `data.sources.<source_name>` to a concrete dataset:
  - file(s) (CSV/Parquet)
  - warehouse tables (Snowflake/BigQuery/Postgres)
  - APIs (SIEM/PAM/etc.)
  - streams

3. **Resolution**: the engine loads those datasets, checks they match the declared `schema`, and resolves each `data.feature_mapping` entry (e.g., `pam.vault_access`) into a concrete feature vector/column.

4. **Execution**: the engine runs the model (`model.frequency`, `model.severity`, dependencies, pipeline) using the resolved/bound feature data. Some engines MAY also support a fallback mode that runs using synthetic data or expert-provided inputs when real telemetry is unavailable.

5. **Outputs**: the engine produces requested metrics and exports (from `output`). If currencies are involved, conversion is applied using an external FX configuration supplied at execution time.

## 1. Changes from CRML 1.0

CRML 1.1 is backward compatible with CRML 1.0 documents in the sense that engines SHOULD continue to accept documents declaring `crml: "1.0"`.

CRML 1.1 adds and/or clarifies:

1. **Median-based lognormal severity parameterization**: `median` is supported and RECOMMENDED over `mu`.
2. **Single-loss auto-calibration for lognormal severity**: `single_losses` MAY be provided as raw incident loss data; engines can derive calibrated lognormal parameters from it.
3. **Explicit currency declaration** for monetary values (via ISO 4217 `currency`).
4. **Readable monetary numbers**: certain monetary fields MAY be written as strings containing spaces as thousands separators.
5. **External FX configuration**: currency conversion is handled out-of-band via an FX config file (engine/CLI option), not embedded into the risk model.

## 2. Document Format

### 2.1 Serialization

A CRML document MUST be a single YAML or JSON object.

### 2.2 Version Declaration

Every CRML document MUST declare the specification version via the top-level `crml` field.

```yaml
crml: "1.1"
```

Consumers MUST reject documents that do not provide the `crml` field.

## 3. Top-level Structure

A CRML document is a single object with the following top-level keys:

```yaml
crml: "1.1"   # required

meta:         # required
data:         # optional
model:        # required
pipeline:     # optional
output:       # optional
```

Unknown top-level keys MAY appear in later versions; engines MAY ignore unknown keys.

## 4. `meta`

The `meta` object describes human-facing identification and categorization.

### 4.1 Required fields

`meta.name` MUST be present and MUST be a string.

### 4.2 Common optional fields

Engines SHOULD preserve these fields for reporting:

```yaml
meta:
  name: "ransomware-scenario"
  version: "2025.1"
  description: "Real-world ransomware risk model"
  author: "Risk Team"
  organization: "Example Corp"
  tags: ["ransomware", "enterprise", "fair-compatible"]
  industries:
    - all
  locale:
    regions: ["world"]
  company_size: ["enterprise"]
  regulatory_frameworks: ["nist-csf", "iso-27001"]
```


`meta.locale` MUST be an object. Both `regions` and `countries` are optional.

If provided, `meta.locale.countries` MUST be an array of **ISO 3166-1 alpha-2** country codes (uppercase), e.g. `["DE", "US"]`.

Examples:

```yaml
meta:
  name: "ransomware-scenario"
  locale: {}
```

```yaml
meta:
  name: "ransomware-scenario"
  locale:
    regions: ["europe"]
```

```yaml
meta:
  name: "ransomware-scenario"
  locale:
    countries: ["DE"]
```

```yaml
meta:
  name: "ransomware-scenario"
  locale:
    regions: ["europe"]
    countries: ["DE"]
```

`meta` MAY contain additional keys not listed above.

## 5. `data` (optional)

The `data` block describes telemetry sources and derived feature mappings that may feed the model.

### 5.1 `data.sources`

`data.sources` is an object whose keys are source names (e.g., `pam`, `dlp`). Each source SHOULD contain:

- `type`: a string indicating the source type (e.g., `pam`, `dlp`, `iam`, `siem`, `custom`).
- `data_schema`: an object mapping field names to primitive types (`int`, `float`, `string`, `bool`, `datetime`).

Example:

```yaml
data:
  sources:
    pam:
      type: pam
      data_schema:
        priv_escalations: int
        failed_sudo: int
        vault_access: int
```

### 5.2 `data.feature_mapping`

`data.feature_mapping` is an object that maps **logical feature names** (the names your model references) to **physical selectors** in the configured `data.sources`.

In CRML 1.1 schema-compliant documents, each mapping value MUST be a source path of the form:

- `source_name.field_name`

where:

- `source_name` is a key under `data.sources` (e.g., `pam`, `dlp`)
- `field_name` is a key under that source’s `schema`

Conceptually:

1. `data.sources` declares “what data exists and its shape”.
2. `data.feature_mapping` declares “which fields (from which sources) the model will use, and what names the model will use for them”.

At execution time, engines bind each `data.sources.<source_name>` to some real dataset (API, file, warehouse table, stream, etc.). The CRML document does not prescribe how.

#### 5.2.1 Basic example

```yaml
data:
  sources:
    pam:
      type: pam
      data_schema:
        priv_escalations: int
        vault_access: int

  feature_mapping:
    priv_escalations: pam.priv_escalations
    vault_access: pam.vault_access
```

In this example, the model can refer to `priv_escalations` and `vault_access` without hard-coding which telemetry system provides them.

#### 5.2.2 Using mapped features in the model

The most common place mapped features show up in CRML 1.1 is `model.assets.criticality_index.inputs`.

In this spec, `inputs` is a mapping from an engine-level “input slot name” (left side) to a feature name defined in `data.feature_mapping` (right side).

Example:

```yaml
data:
  sources:
    pam:
      type: pam
      data_schema:
        pam_entropy: float
    dlp:
      type: dlp
      data_schema:
        channel_entropy: float

  feature_mapping:
    pam_entropy: pam.pam_entropy
    dlp_entropy: dlp.channel_entropy

model:
  assets:
    cardinality: 18000
    criticality_index:
      type: entropy-weighted
      inputs:
        pam_entropy: pam_entropy
        dlp_entropy: dlp_entropy
      weights:
        pam_entropy: 0.6
        dlp_entropy: 0.4
      transform: "clip(1 + 4 * total_entropy, 1, 5)"
```

Engines SHOULD error if `criticality_index.inputs` references a feature name that is not present in `data.feature_mapping`.

#### 5.2.3 Validation and engine extensions

Some documentation and engines use expression-like feature mappings (e.g., `"entropy(pam.*)"`). These can be useful, but they are **engine-specific**.

- For strict CRML 1.1 schema compliance, mapping values MUST be `source.field` paths.
- Engines MAY support richer expressions, but such documents MAY fail strict schema validation.

If you need computed/derived features while remaining schema-compliant, the simplest approach is to compute them outside CRML and expose the computed result as a concrete `source.field`.

## 6. `model`

The `model` object is the core of CRML. It MUST include both `frequency` and `severity`.

### 6.1 `model.assets` (optional)

`model.assets` describes the portfolio being modeled.

```yaml
model:
  assets:
    cardinality: 500
```

If a frequency model uses `scope: asset`, `assets.cardinality` SHOULD be provided.

#### 6.1.1 `criticality_index` (optional)

If present, `assets.criticality_index` describes how to compute an asset criticality score (often 1–5).

```yaml
model:
  assets:
    criticality_index:
      type: entropy-weighted
      inputs:
        pam_entropy: pam_entropy
      weights:
        pam_entropy: 1.0
      transform: "clip(1 + 4 * total_entropy, 1, 5)"
```

Engines MAY treat `transform` as an engine-specific expression language.

### 6.2 `model.frequency`

`model.frequency` defines how often loss events occur.

Required:
- `model.frequency.model` MUST be one of: `poisson`, `negative_binomial`, `hierarchical_gamma_poisson`, `zero_inflated_poisson`.

Optional:
- `model.frequency.scope` MAY be `portfolio` (default) or `asset`.

Example:

```yaml
model:
  frequency:
    model: poisson
    scope: asset
    parameters:
      lambda: 0.08
```

Parameters MAY be numbers or (engine-specific) expressions. Implementations MAY support expressions referencing a criticality index variable such as `CI`.

### 6.3 `model.severity`

`model.severity` defines the magnitude of loss per event.

Required:
- `model.severity.model` MUST be one of: `lognormal`, `gamma`, `mixture`, `pareto`, `weibull`.

#### 6.3.1 Lognormal parameterization (CRML 1.1)

For `lognormal`, `parameters` MUST provide exactly one of:

- (`median` (RECOMMENDED) and `sigma`), or
- (`mu` (ADVANCED) and `sigma`), or
- `single_losses` (auto-calibration input)

If `single_losses` is used, it MUST replace `median`, `mu`, and `sigma`.

Median-based (RECOMMENDED):

```yaml
model:
  severity:
    model: lognormal
    parameters:
      median: "700 000"
      currency: USD
      sigma: 1.8
```

Mu-based (ADVANCED):

```yaml
model:
  severity:
    model: lognormal
    parameters:
      mu: 12.43
      sigma: 1.2
```

Single-loss auto-calibration (AUDITABLE INPUT):

```yaml
model:
  severity:
    model: lognormal
    parameters:
      currency: USD
      single_losses:
        - "25 000"
        - "18 000"
        - "45 000"
        - "32 000"
```

Implementations MUST reject a lognormal `parameters` object that:

- contains both `median` and `mu`, or
- contains `single_losses` alongside any of `median`, `mu`, or `sigma`.

Relationship:

$$\mu = \ln(\mathrm{median}) \qquad \mathrm{median} = e^{\mu}$$

For `single_losses`, an implementation MAY derive calibrated parameters from the data. The reference runtime computes:

$$\mu = \ln(\mathrm{median}(\text{single\_losses}))$$

$$\sigma = \mathrm{stddev}(\ln(\text{single\_losses}))$$

#### 6.3.2 Currency declaration

If a severity parameter represents a monetary quantity, the document SHOULD declare its ISO 4217 currency code via `currency`.

CRML itself does not embed FX rates. Currency conversion is an execution concern handled (in the reference runtime) via an external FX configuration.

#### 6.3.3 Readable monetary numbers (space-separated thousands)

Some implementations (including the reference runtime) accept large monetary values as strings containing spaces as thousands separators.

Rules:
- Only digits and spaces SHOULD be used (e.g., `"1 000 000"`).
- Commas and locale-specific decimal separators SHOULD NOT be used.

This format MAY be used for monetary inputs such as `median` and individual values within `single_losses`.

Note: Strict validators may only allow this format for fields that explicitly permit it.

#### 6.3.4 Mixture severity

For `model: mixture`, `components` is an array of component distributions. Each element MUST be an object with exactly one key whose name is the distribution type (e.g., `lognormal`, `gamma`). Each component MUST include a `weight` in `[0, 1]`.

Implementations SHOULD warn if the sum of all component weights is not approximately 1.0.

Example:

```yaml
model:
  severity:
    model: mixture
    components:
      - lognormal:
          weight: 0.7
          median: "162 755"
          currency: USD
          sigma: 1.2
      - gamma:
          weight: 0.3
          shape: 2.5
          scale: 10000
```

### 6.4 `model.dependency` (optional)

By default, many models assume different risk drivers are independent. In real life, they often are not: the same “bad year” (active attacker campaigns, weak controls, major outages) can increase multiple types of loss at the same time.

The `model.dependency` block lets a model *optionally* tell an engine that some parts of the model should move together (be correlated). This is most commonly represented with a **copula**, which is a standard way to describe “how variables are correlated” without changing each variable’s own distribution.

In plain terms: you keep your frequency/severity distributions as-is, and the copula tells the engine how to make multiple random factors rise/fall together.

```yaml
model:
  dependency:
    copula:
      type: gaussian
      dimension: 4
      rho_matrix: "toeplitz(0.7, 4)"
```

Interpretation:

- `dimension` is how many correlated factors you want the engine to couple.
- `rho_matrix` describes how strongly those factors move together (higher values = more “shared bad years”).

toeplitz(0.7, 4) is a shorthand for generating a simple 4×4 correlation matrix where correlations decay as things get “further apart” in index.

In plain terms: it’s saying “I have 4 factors, and factor 1 is strongly correlated with factor 2, a bit less with factor 3, even less with factor 4”, and the pattern repeats symmetrically.

Example with an explicit correlation matrix:

```yaml
model:
  dependency:
    copula:
      type: gaussian
      dimension: 3
      rho_matrix:
        - [1.0, 0.6, 0.2]
        - [0.6, 1.0, 0.4]
        - [0.2, 0.4, 1.0]
```

Note: the exact meaning of the “factors” being coupled (e.g., threat categories, business units, latent risk drivers) is engine-defined. Engines that do not implement dependency handling MAY ignore this block but MUST inform the user that it was ignored.

### 6.5 `model.temporal` (optional)

Time settings MAY be provided:

```yaml
model:
  temporal:
    horizon: "12m"
    granularity: "1m"
```

Meaning:

- `horizon` is the **total time span** the model intends to describe/simulate. Example: `"12m"` means a one-year horizon; `"24m"` means two years.
- `granularity` is the **time step** used for time-sliced simulation or reporting. Example: `"1m"` means monthly steps; `"1w"` weekly steps.

CRML is commonly used with **annualized** frequency and severity assumptions (e.g., a Poisson `lambda` interpreted as “events per year”). In that common case:

- `horizon: "12m"` corresponds to an annual horizon and metrics like `EAL` are naturally “per year”.
- If the horizon is longer (e.g., `"24m"`), engines SHOULD define whether results are reported for the full horizon or normalized back to an annual basis.

Engines MAY ignore `model.temporal` if they do not support time-stepped simulation, but they SHOULD document how they interpret (or ignore) these fields.

Both `horizon` and `granularity` use the format `<number><unit>` where unit is one of: `d`, `w`, `m`, `y`.

If `model.temporal` is not defined, engines SHOULD assume an annual `granularity` and a `horizon` of 10 years.

## 7. `pipeline` (optional)

`pipeline` configures simulation and validation.

```yaml
pipeline:
  simulation:
    monte_carlo:
      enabled: true
      runs: 10000
      random_seed: 42
    mcmc:
      enabled: false
  validation:
    mcmc:
      rhat_threshold: 1.05
      ess_min: 1000
```

Engines MAY ignore pipeline configuration fields they do not implement.

## 8. `output` (optional)

`output` describes requested metrics and export formats.

```yaml
output:
  metrics: ["EAL", "VaR_95", "VaR_99"]
  distributions:
    annual_loss: true
  export:
    csv: "results.csv"
    json: "results.json"
```

## 9. External FX Configuration (execution-time)

Currency conversion is defined outside CRML models to keep risk models stable and auditable.

The reference CLI/runtime supports an FX config file with:

```yaml
base_currency: USD
output_currency: EUR
as_of: "2025-01-15"   # optional
rates:
  EUR: 1.08
  GBP: 1.26
  JPY: 0.0066
```

and the CLI flag:

```bash
crml simulate model.yaml --fx-config fx-config.yaml
```

Implementation note (reference runtime): rates are interpreted using the convention “1 unit of currency = X USD (as base)”.

## 10. Validation

CRML 1.1 documents SHOULD validate against the JSON Schema shipped with this repository.

Example:

```bash
crml validate spec/examples/data-breach-simple.yaml
```

## 11. Migration Guide (CRML 1.0 → 1.1)

1. Update the version declaration:

```yaml
crml: "1.1"
```

2. For lognormal severity, prefer `median` and compute it from `mu` if needed:

$$\mathrm{median} = e^{\mu}$$

Alternatively, if you have incident loss samples, you MAY provide `single_losses` and let the engine auto-calibrate `mu` and `sigma`.

3. Add `currency` to monetary parameters.

4. If combining multiple currencies, provide an external FX config and pass it at execution time.

## 12. Examples

See `spec/examples/` for complete CRML 1.1 models.
