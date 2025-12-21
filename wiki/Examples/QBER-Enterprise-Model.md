# Example: QBER-style Enterprise Model

This page describes how to represent a “QBER-inspired” enterprise model using CRML documents.

## Risk management approach

Use this approach when you want to combine:

- a portfolio/inventory view of the enterprise (assets/exposure)
- richer frequency/severity model choices (often Bayesian/hierarchical)
- traceable assumptions and inputs (data sources, feature mappings)

## What CRML can express vs what is engine/tool-defined

CRML can express:

- Scenario structure: frequency model ID + parameters, severity model ID + parameters/components.
- Optional data source metadata and feature mapping.
- Portfolio structure: assets, scenario references, aggregation semantics, optional relationships/dependencies.

Engine/tool-defined (not standardized by CRML):

- The semantics of specific model IDs (e.g., `hierarchical_gamma_poisson`).
- How “criticality index” is computed and how it influences model parameters.
- Any Bayesian inference / MCMC pipeline and diagnostics.

In CRML Studio, treat engine/tool-defined pieces as a project-level contract: choose an engine that supports the model IDs you use, and keep the assumptions visible.

## Example scenario (QBER-inspired)

```yaml
crml_scenario: "1.0"
meta:
  name: "qber-inspired"
  version: "2025.1"
  description: "QBER-inspired: hierarchical frequency + mixture severity (engine-defined)."
data:
  sources:
    pam:
      type: pam
      data_schema:
        priv_escalations: int
        rotation_failures: int
  feature_mapping:
    pam_entropy: pam.pam_entropy
scenario:
  frequency:
    basis: per_organization_per_year
    model: hierarchical_gamma_poisson
    parameters:
      alpha_base: 2.0
      beta_base: 1.0
  severity:
    model: mixture
    parameters: {}
    components:
      - lognormal:
          weight: 0.7
          median: "162 755"
          currency: USD
          sigma: 1.2
      - gamma:
          weight: 0.3
          shape: 2.5
          scale: "10 000"
          currency: USD
```

## Example portfolio (enterprise exposure + aggregation)

```yaml
crml_portfolio: "1.0"
meta:
  name: "enterprise-qber-inspired"
portfolio:
  semantics:
    method: sum
    constraints:
      validate_scenarios: true

  assets:
    - name: endpoints
      cardinality: 10000
      tags: [it, endpoint]
      criticality_index:
        type: entropy-weighted
        inputs:
          pam_entropy: pam_entropy
        weights:
          pam_entropy: 1.0

  scenarios:
    - id: enterprise_loss
      path: ./qber-inspired.yaml
```

## What is possible (today)

- You can represent “QBER-style” structure and assumptions as CRML documents.
- You can keep the engine-specific logic outside the language while still making it auditable.
- You can combine the model with control catalogs/assessments in the portfolio to express posture.

## Limitations / assumptions

- CRML does not define how Bayesian inference is performed; engines/tools decide.
- Some engines will ignore or partially support complex component structures.
- Any link between asset criticality and model parameters is engine-defined and must be documented.
