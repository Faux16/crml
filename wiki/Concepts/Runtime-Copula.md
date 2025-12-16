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

In CRML 1.1, dependencies are expressed via `model.dependency` (see the specification).
Different engines may implement this with different copula mechanisms.

The reference engine (`crml_engine`) currently supports correlation across scenarios using an engine-specific `model.correlations` list (correlated uniforms applied to frequency sampling).

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
