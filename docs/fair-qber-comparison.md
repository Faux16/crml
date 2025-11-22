# FAIR vs QBER in CRML

This page compares FAIR-style models and QBER-style models, and shows how CRML
can represent both.

---

## 1. FAIR-style (non-Bayesian Monte Carlo)

Characteristics:

- Inputs: TEF, VF, LM (primary/secondary)
- Frequency: deterministic or PERT/traditional distributions
- Severity: lognormal (or similar)
- Independence assumptions by default
- No explicit Bayesian updating

In CRML, this maps to:

- simple `poisson` frequency
- single `lognormal` severity
- no `dependency` section

See: [Example: FAIR Baseline](models/example-fair-baseline.md).

---

## 2. QBER-style (Bayesian hierarchical + MCMC)

Characteristics:

- Hierarchical Gamma–Poisson for frequency
- Mixture severity with heavy tails
- Copula dependencies across components
- Entropy-based criticality indices
- Bayesian posterior inference (MCMC)

In CRML, this maps to:

- `hierarchical_gamma_poisson` frequency
- `mixture` severity
- `dependency.copula` defined
- `assets.criticality_index` defined

See: [Example: QBER Enterprise](models/example-qber-enterprise.md).

---

## 3. Key differences

| Aspect             | FAIR-style                   | QBER-style                           |
|--------------------|------------------------------|--------------------------------------|
| Frequency          | TEF, VF → point or simple MC | Gamma–Poisson, hierarchical          |
| Severity           | Single lognormal             | Mixture (lognormal + Gamma, etc.)    |
| Dependencies       | Often ignored                | Explicit copulas                     |
| Updating           | Typically static             | Bayesian updates (MCMC)              |
| Tail modeling      | Limited by LM params         | Rich heavy-tailed, multi-modal       |

CRML is agnostic: it provides the *language* to describe either style (or
hybrids) and lets the runtime implement the appropriate math.
