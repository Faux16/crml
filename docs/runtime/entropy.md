# Entropy & Criticality

CRML supports **entropy-based asset criticality** as a bridge between
security-control telemetry and risk parameters.

---

## 1. Shannon entropy

Given category counts \(c_1, \dots, c_K\) (e.g., counts of different alert
types or states), define probabilities:

\[
p_k = \frac{c_k}{\sum_{j=1}^K c_j}
\]

The Shannon entropy is:

\[
H = - \sum_{k=1}^K p_k \log_2 p_k
\]

- Higher \(H\) = more *uncertainty* / *disorder* in the signal.
- Lower \(H\) = more concentrated behavior.

Reference runtime:

```python
from crml.entropy import entropy_from_counts

counts = {"normal": 900, "failed": 80, "anomalous": 20}
H = entropy_from_counts(counts)
```

---

## 2. Entropy-based criticality index (CI)

CRML often maps entropy features into a **Criticality Index (CI)**:

\[
\text{CI}_i = g\left( \sum_f w_f H_f(i) \right)
\]

where:

- \(H_f(i)\) is the entropy of feature family \(f\) for asset \(i\)
- \(w_f\) are weights (sum to 1)
- \(g\) is a squashing/transform function (e.g., clip to [1, 5])

Example in CRML:

```yaml
model:
  assets:
    cardinality: 18000
    criticality_index:
      type: entropy-weighted
      inputs:
        - pam_entropy
        - dlp_entropy
        - iam_entropy
      weights:
        pam_entropy: 0.4
        dlp_entropy: 0.3
        iam_entropy: 0.3
      transform: "clip(1 + total_entropy * 3, 1, 5)"
```

---

## 3. Using CI in frequency/severity

A QBER-style model might derive frequency parameters from CI:

\[
\alpha_i = \alpha_0 + c_1 \cdot \text{CI}_i, \quad
\beta_i = \beta_0 + c_2 \cdot \text{CI}_i
\]

CRML does not hard-code the formula in the spec; instead, it leaves room for
runtime implementations to incorporate CI in:

- `frequency.parameters.alpha_base`
- `frequency.parameters.beta_base`
- or in extensions to hierarchical models.

This keeps the **specification clean** while allowing **Bayesian richness** in
implementations.
