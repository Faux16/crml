# Best-practice CRML Models

This page outlines patterns observed in robust enterprise risk models.

---

## 1. Separate data, model, and outputs

Good CRML models usually keep:

- `data`: purely about sources and features
- `model`: purely about distributions and dependencies
- `output`: purely about metrics and export formats

Avoid mixing telemetry-specific assumptions into the `model` section.

---

## 2. Use Gamma–Poisson for enterprise event rates

Empirical studies suggest that **breach counts** and **incident rates** are
over-dispersed across organizations and assets.

Recommendation:

```yaml
model:
  frequency:
    model: gamma_poisson
    parameters:
      alpha_base: 1.0
      beta_base: 1.0
```

Then, refine based on observed frequencies.

---

## 3. Use mixtures for loss severity

Single lognormals often underfit:

- small operational events
- catastrophic outliers

Mixtures help:

```yaml
model:
  severity:
    model: mixture
    components:
      - lognormal:
          weight: 0.7
          mu: 12.0
          sigma: 1.2
      - gamma:
          weight: 0.3
          shape: 2.5
          scale: 20000.0
```

---

## 4. Make correlations explicit

It is better to specify:

```yaml
dependency:
  copula:
    type: gaussian
    dim: 4
    rho: 0.6
```

than to silently assume independence across components.

---

## 5. Version your CRML models

Use `meta.version` to align CRML files with:

- internal policy versions
- regulatory submissions
- release cycles

Example:

```yaml
meta:
  name: "banking-risk-core"
  version: "2025.1"
  description: "Core enterprise cyber risk model v2025.1"
```
