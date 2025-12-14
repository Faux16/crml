# CRML 1.1 — Cyber Risk Modeling Language

**Status:** Draft  
**Version:** 1.1  
**Origin:** Zeron Research Labs  

CRML (Cyber Risk Modeling Language) is a declarative, implementation-agnostic
language for defining end-to-end cyber risk models and their execution
pipelines. CRML documents are written in YAML or JSON and are designed to be
consumed by different execution engines (e.g., QBER, FAIR-style Monte Carlo,
insurer risk engines).

## 1. Top-Level Structure

A CRML document is a single YAML/JSON object with these top-level keys:

```yaml
crml: "1.1"

meta:       # metadata (who, what, why)
data:       # telemetry sources and feature mapping
model:      # frequency, severity, dependencies, asset models
pipeline:   # simulation, validation
output:     # requested metrics, artifacts, exports
```

Only `crml`, `meta`, and `model` are strictly required.

## 2. Meta Block

```yaml
meta:
  name: "string"            # required
  version: "string"         # optional
  description: "string"     # optional
  author: "string"          # optional
  organization: "string"    # optional
  tags:                     # optional
    - "qber"
    - "fair-compatible"
```

## 3. Currency Handling

CRML supports explicit currency declarations on monetary parameters. Currency 
conversion and output preferences are handled externally via FX configuration 
files, keeping the risk model focused on risk parameters.

### In CRML Models

Monetary parameters can declare their currency:

```yaml
severity:
  model: lognormal
  parameters:
    median: "100 000"  # €100K typical loss
    currency: EUR      # explicit currency code
    sigma: 1.2
```

### FX Configuration (External)

Currency conversion is handled via a separate FX config file:

```yaml
# fx-config.yaml
base_currency: USD        # internal calculation currency
output_currency: EUR      # display results in Euros
as_of: "2025-01-15"       # informative: when rates were captured
rates:
  EUR: 1.08
  GBP: 1.26
  CHF: 1.12
```

Usage:
```bash
crml simulate model.yaml --fx-config fx-config.yaml
```

This separation provides:

- **Clean models** - Risk models focus on risk, not FX rates
- **Single source of truth** - Update rates in one place
- **Reproducibility** - FX rates are explicit and versioned

## 4. Data Block

Describes security tool sources (e.g., PAM, DLP, IAM, XDR, WAF).

```yaml
data:
  sources:
    pam:
      type: "pam"
      schema:
        priv_escalations: "int"
        failed_sudo: "int"
        vault_access: "int"
        rotation_failures: "int"
  feature_mapping:
    pam_entropy: "pam.pam_entropy"
```

Engines may bind these to real tables/streams or synthesize them.

## 5. Model Block

```yaml
model:
  assets:
    cardinality: 10000
    criticality_index:
      type: "entropy-weighted"
      inputs:
        pam_entropy: "pam_entropy"
      weights:
        pam_entropy: 1.0
      transform: "clip(1 + 4 * total_entropy, 1, 5)"

  frequency:
    model: "hierarchical_gamma_poisson"
    scope: "asset"
    parameters:
      alpha_base: "1 + CI * 0.5"
      beta_base: 1.5

  severity:
    model: "lognormal"
    parameters:
      median: "250 000"   # human-readable median loss value
      currency: EUR       # explicit currency declaration
      sigma: 1.2

  # Alternative: mixture model
  # severity:
  #   model: "mixture"
  #   components:
  #     - lognormal:
  #         weight: 0.7
  #         median: "162 755"
  #         currency: USD
  #         sigma: 1.2
  #     - gamma:
  #         weight: 0.3
  #         shape: 2.5
  #         scale: 10000

  dependency:
    copula:
      type: "gaussian"
      dimension: 4
      rho_matrix: "toeplitz(0.7, 4)"

  temporal:
    horizon: "24m"
    granularity: "1m"
```

### Severity Parameters

For lognormal distributions, CRML supports two parameterization modes:

**Mode A: Median-based (recommended)**
```yaml
severity:
  model: lognormal
  parameters:
    median: "250 000"  # human-readable median loss
    currency: EUR      # explicit currency
    sigma: 1.2
```

**Mode B: Mu-based (advanced)**
```yaml
severity:
  model: lognormal
  parameters:
    mu: 12.43        # ln(median) - less intuitive
    sigma: 1.2
```

The median-based approach is recommended because:
- Median values come directly from industry reports and expert elicitation
- No manual log transformation required
- More readable and auditable by non-statisticians

## 6. Pipeline Block

```yaml
pipeline:
  simulation:
    monte_carlo:
      enabled: true
      runs: 20000
      random_seed: 42
    mcmc:
      enabled: true
      algorithm: "metropolis_hastings"
      iterations: 15000
      burn_in: 3000
      chains: 4

  validation:
    mcmc:
      rhat_threshold: 1.05
      ess_min: 5000
```

## 7. Output Block

```yaml
output:
  metrics:
    - "EAL"
    - "VaR_95"
    - "VaR_99"
  distributions:
    annual_loss: true
  export:
    csv: "results.csv"
    json: "results.json"
```

See `spec/examples/` for complete CRML examples.
