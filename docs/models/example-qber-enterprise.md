# Example: QBER-style Enterprise Model

This example captures a QBER-like enterprise cyber risk model in CRML form.

```yaml
crml: "1.1"

meta:
  name: "qber-enterprise"
  description: "QBER-style hierarchical Gamma–Poisson with mixture severity."
  version: "2025.1"

model:
  assets:
    cardinality: 10000
    criticality_index:
      type: entropy-weighted
      inputs:
        - pam_entropy
        - dlp_entropy
        - iam_entropy
      weights:
        pam_entropy: 0.3
        dlp_entropy: 0.3
        iam_entropy: 0.4
      transform: "clip(1 + total_entropy * 3, 1, 5)"

  frequency:
    model: hierarchical_gamma_poisson
    parameters:
      alpha_base: 0.8
      beta_base: 1.3

  severity:
    model: mixture
    components:
      - lognormal:
          weight: 0.7
          mu: 12.0
          sigma: 1.25
      - gamma:
          weight: 0.3
          shape: 2.8
          scale: 15000.0

  dependency:
    copula:
      type: gaussian
      dim: 4
      rho: 0.65

output:
  metrics:
    - EAL
    - VaR_95
    - VaR_99
    - VaR_999
  distributions:
    annual_loss: true
```

You can run this via:

```bash
crml run qber-enterprise.yaml --runs 30000
```
