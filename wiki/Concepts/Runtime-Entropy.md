# Runtime (Entropy)

This page is a conceptual reference for entropy-style measures.

Entropy can be used to summarize uncertainty, dispersion, or heterogeneity.

---

## Shannon entropy (concept)

For a discrete distribution with probabilities $p_i$:

$$
H = -\sum_i p_i \log p_i
$$

For continuous variables, differential entropy exists but is not directly comparable across unit changes.

---

## Reference engine status

The reference engine in this repo does **not** currently compute entropy-based risk metrics as first-class outputs.

What it *does* have today:

- A **planning-time warning** when a bound asset set appears heterogeneous (tags and/or `criticality_index.type` differ). This is used as a guardrail, not as an entropy measure.

If you want entropy-based measures in results, they should be treated as an engine-defined extension.
