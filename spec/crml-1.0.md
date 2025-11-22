# CRML 1.0 — Cyber Risk Modeling Language

**Status:** Draft  
**Version:** 1.0  
**Origin:** Zeron Research Labs  

CRML (Cyber Risk Modeling Language) is a declarative, implementation-agnostic
language for defining end-to-end cyber risk models and their execution
pipelines. CRML documents are written in YAML or JSON and are designed to be
consumed by different execution engines (e.g., QBER, FAIR-style Monte Carlo,
insurer risk engines).

## 1. Top-Level Structure

A CRML document is a single YAML/JSON object with these top-level keys:

```yaml
crml: "1.0"

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

## 3. Data Block

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

## 4. Model Block

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
    model: "mixture"
    components:
      - lognormal:
          weight: 0.7
          mu: 12
          sigma: 1.2
      - gamma:
          weight: 0.3
          shape: 2.5
          scale: 10000

  dependency:
    copula:
      type: "gaussian"
      dimension: 4
      rho_matrix: "toeplitz(0.7, 4)"

  temporal:
    horizon: "24m"
    granularity: "1m"
```

## 5. Pipeline Block

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

## 6. Output Block

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
