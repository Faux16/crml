# Deep Mathematics

This page collects deeper mathematical background for CRML-style risk simulation.

CRML is designed so the **language** stays stable while engines can evolve their algorithms.

---

## The core simulation loop

A common annual-loss simulation structure is:

1. Sample event count $N$ from a frequency model.
2. Sample severities $X_1, \dots, X_N$ from a severity model.
3. Aggregate annual loss $L = \sum_{i=1}^{N} X_i$.

Engines may add layers such as control multipliers, dependence structures, or hierarchical modeling.

---

## Heavy tails and percentiles

Risk reporting often focuses on:

- Expected annual loss (EAL): $\mathbb{E}[L]$
- Value at Risk: $\text{VaR}_{p}(L)$, e.g. $p=0.95, 0.99$

Percentiles are sensitive to tail behavior and require sufficient simulation runs for stability.

---

## Dependence

Dependence structures (e.g., copulas) can materially change tail risk.

See: [Runtime (Copula)](Runtime-Copula.md)

---

## Reference engine status

For what the reference engine supports today (models, controls, portfolios), see:

- [Engine capabilities: Supported models](../Engine/Capabilities/Supported-Models.md)
