# CRML Examples

This directory contains example CRML 1.1 models

- `data-breach-simple.yaml` — Simple data breach model with 50 databases, 5% annual probability, $100K median loss
- `ransomware-scenario.yaml` — Enterprise ransomware risk with 500 servers, 8% probability, $700K median loss
- `fair-baseline.yaml` — Simple FAIR-like model using Poisson frequency and Lognormal severity with median-based parameterization
- `qber-simplified.yaml` — Simplified QBER-style model with mixture severity distribution
- `qber-enterprise.yaml` — Full QBER-style hierarchical Bayesian model with entropy-based Criticality Index, mixture severity, Gaussian copula, and MCMC + Monte Carlo pipeline

## Key Changes in CRML 1.1

### Median-Based Parameterization
Instead of using `mu` (log-space mean), models now support `median` directly:

```yaml
severity:
  model: lognormal
  parameters:
    median: "100 000"  # $100K - intuitive!
    currency: USD
    sigma: 1.2
```

### Explicit Currency Declaration
All monetary parameters should declare their currency:

```yaml
severity:
  model: lognormal
  parameters:
    median: "250 000"
    currency: EUR   # Explicit currency
    sigma: 1.2
```

### FX Context (Optional)
For multi-currency models, define an FX context:

```yaml
fx_context:
  base_currency: EUR
  rates:
    USD: 0.92
    GBP: 1.17
```

See the [specification](../crml-1.1.md) for full details.
