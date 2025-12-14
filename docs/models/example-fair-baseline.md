# Example: FAIR-style Baseline Model

This example encodes a FAIR-like single-scenario model with:

- simple Poisson frequency
- lognormal loss magnitude

```yaml
crml: "1.1"

meta:
  name: "fair-baseline"
  description: "FAIR-like baseline model expressed in CRML."
  version: "2025.1"

model:
  assets:
    cardinality: 1    # single scenario

  frequency:
    model: poisson
    parameters:
      lambda: 0.4     # expected events per year

  severity:
    model: lognormal
    parameters:
      mu: 11.0
      sigma: 1.0

output:
  metrics:
    - EAL
    - VaR_95
    - VaR_99
```

This is conceptually similar to a FAIR model where:

- TEF ≈ λ
- LM ≈ lognormal magnitude
- LEF = TEF × VF can be folded into λ or severity scale.
