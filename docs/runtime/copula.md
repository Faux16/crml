# Copula Dependencies

CRML uses **Gaussian copulas** to model dependencies between risk components
(threat classes, business units, etc.).

---

## 1. Gaussian copula construction

1. Sample \(Z \sim \mathcal{N}(0, \Sigma)\), where \(\Sigma\) is a
   correlation matrix.
2. Map each component \(Z_k\) to a uniform:

\[
U_k = \Phi(Z_k)
\]

where \(\Phi\) is the standard normal CDF.

3. Obtain dependent losses:

\[
L_k = F_k^{-1}(U_k)
\]

where \(F_k\) is the marginal CDF of component \(k\) (e.g., its loss
distribution implied by frequency + severity).

---

## 2. Toeplitz correlation in CRML

CRML uses a simple Toeplitz structure parameterized by \(\rho\):

\[
\Sigma_{ij} = \rho^{|i - j|}
\]

Example:

```yaml
model:
  dependency:
    copula:
      type: gaussian
      dim: 4
      rho: 0.65
```

Runtime prototype:

```python
from crml.copula import gaussian_copula_samples

u = gaussian_copula_samples(rho=0.65, dim=4, n=10000)
```

`u` is a `(n, dim)` matrix of uniforms; each column can be mapped through an
inverse CDF to produce correlated losses.

---

## 3. Why copulas matter for cyber risk

Without dependencies, total loss is often **underestimated**, because models
assume:

- events in different components are independent
- large losses cannot co-occur

Copulas allow:

- joint occurrence of high-severity events in multiple components
- realistic clustering of bad scenarios

CRML makes the presence or absence of copula dependencies **explicit** in the
model file.
