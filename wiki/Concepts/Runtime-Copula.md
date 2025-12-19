# Runtime (Copula)

Copulas are a way to model **dependence** between random variables while keeping marginal distributions unchanged.

In Monte Carlo simulation, a common pattern is:

1. Sample correlated uniforms $(U_1, \dots, U_d)$.
2. Transform each uniform into a marginal sample using the inverse CDF of the marginal distribution.

---

## Gaussian copula (concept)

A Gaussian copula uses a multivariate normal correlation structure:

1. Sample $Z \sim \mathcal{N}(0, \Sigma)$
2. Convert to uniforms: $U_i = \Phi(Z_i)$

where $\Phi$ is the standard normal CDF.

---

## What CRML uses copulas for

The CRML language does not mandate a universal “copula field” for all dependency modeling. Dependency constructs are generally engine/tool-specific.

In this repo, the reference engine supports **correlating control-state sampling** (binary up/down states) via a Gaussian copula specified in `portfolio.dependency.copula`.

See:

- [Engine capabilities: Portfolio execution](../Engine/Capabilities/Portfolio-Execution.md)
- [Engine capabilities: Controls](../Engine/Capabilities/Controls.md)
