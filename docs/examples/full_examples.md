# Full CRML Examples

This page provides complete examples of CRML models, ranging from simple baselines to complex enterprise-grade risk quantification models.

## 1. FAIR Baseline Model

A simple FAIR-like model using Poisson frequency and Lognormal severity with pure Monte Carlo simulation. This is useful for quick estimates and baseline comparisons.

```yaml
crml: '1.1'
meta:
  name: fair-baseline
  version: '1.1'
  description: Simple FAIR-like Poisson + Lognormal model
model:
  frequency:
    model: poisson
    scope: portfolio
    parameters:
      lambda: 1.2
  severity:
    model: lognormal
    parameters:
      median: "8 100"   # ~$8K median loss
      currency: USD
      sigma: 1.0
pipeline:
  simulation:
    monte_carlo:
      enabled: true
      runs: 50000
      random_seed: 7
output:
  metrics:
  - EAL
  - VaR_95
  - VaR_99
  distributions:
    annual_loss: true
```

## 2. QBER Enterprise Model

A comprehensive QBER-style hierarchical Bayesian model. It features:
- **Entropy-based Criticality Index (CI)** derived from multiple security tools (PAM, DLP, IAM, XDR, WAF).
- **Hierarchical Gamma-Poisson** frequency model.
- **Mixture Severity Model** combining Lognormal and Gamma distributions.
- **Gaussian Copula** for dependency modeling.
- **MCMC (Metropolis-Hastings)** and **Monte Carlo** simulation pipeline.

```yaml
crml: '1.1'
meta:
  name: qber-enterprise-v1
  version: '2025.1'
  description: QBER-style hierarchical Bayesian model with entropy-based CI and MCMC
  author: Zeron Research Labs
  tags:
  - qber
  - bayesian
  - mcmc
  - pam
  - dlp
  - iam
  - xdr
  - waf
data:
  sources:
    pam:
      type: pam
      schema:
        priv_escalations: int
        failed_sudo: int
        vault_access: int
        rotation_failures: int
    dlp:
      type: dlp
      schema:
        usb_alerts: int
        dpi_hits: int
        exfil_attempts: int
        channel_entropy: float
    iam:
      type: iam
      schema:
        mfa_failures: int
        role_drift: int
        privilege_anomalies: int
        identity_graph_entropy: float
    xdr:
      type: xdr
      schema:
        malware_detections: int
        lateral_movement: int
        process_tree_entropy: float
    waf:
      type: waf
      schema:
        sqli_attempts: int
        rce_attempts: int
        bot_traffic: int
        request_entropy: float
  feature_mapping:
    pam_entropy: pam.pam_entropy
    dlp_entropy: dlp.channel_entropy
    iam_entropy: iam.identity_graph_entropy
    xdr_entropy: xdr.process_tree_entropy
    waf_entropy: waf.request_entropy
model:
  assets:
    cardinality: 10000
    criticality_index:
      type: entropy-weighted
      inputs:
        pam_entropy: pam_entropy
        dlp_entropy: dlp_entropy
        iam_entropy: iam_entropy
        xdr_entropy: xdr_entropy
        waf_entropy: waf_entropy
      weights:
        pam_entropy: 0.2
        dlp_entropy: 0.2
        iam_entropy: 0.2
        xdr_entropy: 0.2
        waf_entropy: 0.2
      transform: clip(1 + 4 * total_entropy, 1, 5)
  frequency:
    model: hierarchical_gamma_poisson
    scope: asset
    parameters:
      alpha_base: 1 + CI * 0.5
      beta_base: 1.5
      hyperpriors:
        alpha_shape: 2.0
        alpha_rate: 1.0
        beta_shape: 1.0
        beta_rate: 1.0
  severity:
    model: mixture
    components:
    - lognormal:
        weight: 0.7
        median: "162 755"  # ~$163K median
        currency: USD
        sigma: 1.2
    - gamma:
        weight: 0.3
        shape: 2.5
        scale: 10000
  dependency:
    copula:
      type: gaussian
      dimension: 4
      rho_matrix: toeplitz(0.7, 4)
  temporal:
    horizon: 24m
    granularity: 1m
    aggregation:
      model: ridge_regression
      inputs:
      - lambda_interno * E[I_interno]
      - lambda_externo * E[I_externo]
      - lambda_vendor * E[I_vendor]
      target: annual_loss
      ewma_alpha: 0.3
pipeline:
  simulation:
    monte_carlo:
      enabled: true
      runs: 20000
      random_seed: 42
    mcmc:
      enabled: true
      algorithm: metropolis_hastings
      iterations: 15000
      burn_in: 3000
      chains: 4
      thinning: 1
  validation:
    mcmc:
      rhat_threshold: 1.05
      ess_min: 5000
    loss_distribution:
      var_stability_tolerance: 0.02
output:
  metrics:
  - EAL
  - VaR_95
  - VaR_99
  - VaR_999
  distributions:
    annual_loss: true
    component_losses: true
  diagnostics:
    mcmc_trace: true
    rhat: true
  export:
    csv: qber_enterprise_results.csv
    json: qber_posterior.json
    latex_table: qber_results_table.tex
```