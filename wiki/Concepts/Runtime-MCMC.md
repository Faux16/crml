# MCMC & Inference

CRML is an implementation-agnostic language: a CRML document can be executed by different engines.

The reference engine in this repository (`crml_engine`) currently focuses on Monte Carlo simulation.
Bayesian inference (MCMC/HMC/NUTS) is typically provided by separate probabilistic programming systems.

## Metropolis–Hastings (conceptual)

We want to sample from a posterior distribution:

\[
p(\theta \mid \mathcal{D}) \propto p(\mathcal{D} \mid \theta) p(\theta)
\]

Metropolis–Hastings constructs a Markov chain:

1. Start at \(\theta^{(0)}\).
2. Propose \(\theta^* \sim q(\theta^* \mid \theta^{(s-1)})\).
3. Accept \(\theta^*\) with probability

\[
\alpha = \min\left(1,
\frac{p(\mathcal{D}\mid\theta^*) p(\theta^*) q(\theta^{(s-1)} \mid \theta^*)}
     {p(\mathcal{D}\mid\theta^{(s-1)}) p(\theta^{(s-1)}) q(\theta^* \mid \theta^{(s-1)})}
\right)
\]

## How this relates to CRML

CRML documents encode:

- the structure of frequency/severity models
- parameters and hyperparameters that an inference engine may interpret as priors

A more advanced runtime can:

1. Read CRML.
2. Construct a probabilistic model in PyMC, NumPyro, or Stan.
3. Use HMC/NUTS or advanced MCMC rather than MH.

The current MH implementation is intentionally simple to keep the reference
runtime light but **conceptually aligned** to QBER.
