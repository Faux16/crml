# Frequency Models

CRML frequency models describe how often **loss events** occur for assets or
risk components.

---

## 1. Poisson model

Mathematically:

\[
N \sim \text{Poisson}(\lambda)
\]

where:

- \(N\) = number of events in a fixed period (e.g., 1 year)
- \(\lambda > 0\) = expected number of events per period

In CRML:

```yaml
model:
  frequency:
    model: poisson
    parameters:
      lambda: 0.3
```

Runtime mapping (reference implementation):

```python
from crml.frequency import sample_poisson_frequency

freq = sample_poisson_frequency({"lambda": 0.3}, size=n_assets)
```

---

## 2. Gamma–Poisson (Negative Binomial)

To model **over-dispersion** (variance > mean), CRML uses a Gamma–Poisson model:

\[
\lambda \sim \text{Gamma}(\alpha, \beta), \quad
N \mid \lambda \sim \text{Poisson}(\lambda)
\]

Marginally, \(N\) follows a Negative Binomial distribution.

In CRML:

```yaml
model:
  frequency:
    model: gamma_poisson
    parameters:
      alpha_base: 1.2
      beta_base: 1.5
```

Reference runtime:

```python
from crml.frequency import sample_gamma_poisson_frequency

params = {"alpha": 1.2, "beta": 1.5}
freq = sample_gamma_poisson_frequency(params, size=n_assets)
```

---

## 3. Hierarchical Gamma–Poisson (QBER-style)

In QBER-like models, \(\alpha\) and \(\beta\) may themselves depend on
asset-level features (e.g., criticality index CI):

\[
\alpha_i = f_\alpha(\text{CI}_i), \quad
\beta_i = f_\beta(\text{CI}_i)
\]

The full hierarchical model (conceptually):

\[
\begin{aligned}
\lambda_i &\sim \text{Gamma}(\alpha_i, \beta_i) \\
N_i \mid \lambda_i &\sim \text{Poisson}(\lambda_i)
\end{aligned}
\]

CRML expresses only the *base form*:

```yaml
model:
  frequency:
    model: hierarchical_gamma_poisson
    parameters:
      alpha_base: 0.8
      beta_base: 1.3
```

The reference runtime currently interprets this similarly to `gamma_poisson` but
can be extended to use CI-dependent parameters.

---

## 4. Practical guidance

- Use **Poisson** for simple, independent, low-variance event counts.
- Use **Gamma–Poisson** when you observe **fat-tailed** or **over-dispersed**
  count data across assets.
- Use **hierarchical** forms when you have **entropy-based criticality indices**
  or other asset-level features.
