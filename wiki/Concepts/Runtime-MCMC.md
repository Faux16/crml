# Runtime (MCMC)

Markov chain Monte Carlo (MCMC) is a family of algorithms for sampling from posterior distributions.

In risk modeling, MCMC is typically used for **calibration** (inferring uncertain model parameters from data) rather than for the forward Monte Carlo simulation of losses.

---

## Conceptual outline

Given parameters $\theta$ and observed data $D$, Bayesian inference defines:

$$
P(\theta \mid D) \propto P(D \mid \theta)\,P(\theta)
$$

MCMC constructs a Markov chain whose stationary distribution is $P(\theta \mid D)$.

---

## Reference engine status

The reference engine in this repo does **not** implement a general MCMC calibration pipeline today.

If you need calibration, start with:

- Empirical lognormal calibration from `single_losses` (supported): see [Runtime (Severity)](Runtime-Severity.md)

More advanced calibration workflows would be engine/tool-specific.
