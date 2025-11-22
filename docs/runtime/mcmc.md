# MCMC & Inference

While the reference CRML runtime focuses on Monte Carlo simulation, it also
provides a lightweight **Metropolis–Hastings (MH)** engine for 1D parameters.

---

## 1. Metropolis–Hastings in one dimension

We want to sample from a posterior distribution:

\[
p(\theta \mid \mathcal{D}) \propto p(\mathcal{D} \mid \theta) p(\theta)
\]

MH constructs a Markov chain:

1. Start at \(\theta^{(0)}\).
2. At step \(s\), propose \(\theta^* \sim q(\theta^* \mid \theta^{(s-1)})\).
3. Compute the acceptance probability:

\[
\alpha = \min\left(1,
\frac{p(\mathcal{D}\mid\theta^*) p(\theta^*) q(\theta^{(s-1)} \mid \theta^*)}
     {p(\mathcal{D}\mid\theta^{(s-1)}) p(\theta^{(s-1)}) q(\theta^* \mid \theta^{(s-1)})}
\right)
\]

4. Accept with probability \(\alpha\).

In the reference runtime, the proposal is symmetric (normal), so \(q\) cancels.

---

## 2. Reference implementation

```python
from crml.mcmc import metropolis_hastings_1d
import numpy as np

def log_posterior(theta):
    # Example: Normal prior N(0, 10^2) and Normal likelihood around 5
    lp_prior = -0.5 * (theta / 10.0) ** 2
    lp_like = -0.5 * ((theta - 5.0) / 2.0) ** 2
    return lp_prior + lp_like

samples = metropolis_hastings_1d(
    log_posterior,
    initial=0.0,
    steps=5000,
    proposal_std=0.5,
    burn_in=1000,
)
```

---

## 3. How MCMC fits into QBER-style CRML

In a full QBER implementation:

- \(\theta\) could be:
  - a frequency hyperparameter (e.g., \(\alpha\), \(\beta\))
  - a mixture weight
  - a tail index
- The likelihood \(p(\mathcal{D}\mid\theta)\) is computed from observed
  loss data or incident counts.

CRML does not encode the full Bayesian graph; it encodes:

- the *structure* of frequency and severity models
- hyperparameters that a Bayesian runtime could treat as priors

A more advanced runtime can:

1. Read CRML.
2. Construct a probabilistic model in PyMC, NumPyro, or Stan.
3. Use HMC/NUTS or advanced MCMC rather than MH.

The current MH implementation is intentionally simple to keep the reference
runtime light but **conceptually aligned** to QBER.
