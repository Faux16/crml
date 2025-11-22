# Severity Models

Severity models describe the **monetary impact** of individual events.

---

## 1. Lognormal severity

Many cyber losses (breaches, outages) empirically follow a lognormal-like tail:

\[
X \sim \text{Lognormal}(\mu, \sigma)
\]

meaning:

\[
\ln X \sim \mathcal{N}(\mu, \sigma^2)
\]

In CRML:

```yaml
model:
  severity:
    model: lognormal
    parameters:
      mu: 12.0
      sigma: 1.25
```

Runtime:

```python
from crml.severity import sample_lognormal

sev = sample_lognormal({"mu": 12.0, "sigma": 1.25}, size=n_events)
```

---

## 2. Gamma severity

For operational loss tails that are lighter than lognormal, a Gamma model can be
used:

\[
X \sim \text{Gamma}(k, \theta)
\]

with shape parameter \(k\) and scale \(\theta\).

In CRML:

```yaml
model:
  severity:
    model: gamma
    parameters:
      shape: 2.5
      scale: 15000.0
```

---

## 3. Mixture severity (QBER-style)

To capture **multi-modal** or **regime-based** behavior, CRML supports mixtures:

\[
X \sim w_1 f_1(x) + w_2 f_2(x) + \cdots
\]

Example: 2-component mixture of lognormal and gamma:

```yaml
model:
  severity:
    model: mixture
    components:
      - lognormal:
          weight: 0.7
          mu: 12.0
          sigma: 1.25
      - gamma:
          weight: 0.3
          shape: 2.8
          scale: 15000.0
```

Runtime implementation (simplified):

```python
from crml.severity import sample_mixture

sev = sample_mixture(components, size=n_events)
```

---

## 4. From frequency & severity to loss

Total annual loss \(L\) in a Monte Carlo scenario:

\[
L = \sum_{i=1}^{N} X_i
\]

where:

- \(N\) ~ frequency model (Poisson, Gamma–Poisson, ...)
- \(X_i\) ~ severity model (Lognormal, Gamma, Mixture, ...)

The CRML runtime loops over Monte Carlo runs, sampling frequency and severity
and aggregating \(L\).

---

## 5. Heavy tails and VaR

For heavy-tailed lognormal (large \(\sigma\)), tail metrics like VaR are
highly sensitive to:

- the chosen \(\mu, \sigma\)
- the assumed correlations (via copula)
- the mixture weights in hybrid models

CRML makes all of these parameters **explicit and versioned** in the model file.
