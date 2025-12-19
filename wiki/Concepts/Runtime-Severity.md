# Runtime (Severity)

This page explains common severity models used in CRML scenarios.

CRML severity is expressed as:

- `scenario.severity.model`: a model identifier (engine-defined support)
- `scenario.severity.parameters`: model parameters (portable intent; engine may impose constraints)

See: [Scenario schema](../Language/Schemas/Scenario.md)

---

## Lognormal

A lognormal model is common for heavy-tailed loss severities.

If $X$ is the loss per event, then:

$$
\ln X \sim \mathcal{N}(\mu, \sigma^2)
$$

CRML commonly uses a **median-first** parameterization for readability:

- `median`: the median loss ($\text{median}(X)$)
- `sigma`: log-space standard deviation

Relationship between median and $\mu$:

$$
\text{median}(X) = e^{\mu} \quad \Rightarrow \quad \mu = \ln(\text{median}(X))
$$

### Empirical calibration (`single_losses`)

Some engines may support calibrating $(\mu, \sigma)$ from empirical single-event losses.

Reference engine status:

- Calibration helper exists: `crml_engine.runtime.calibrate_lognormal_from_single_losses`.
- You can also provide `single_losses` directly in lognormal parameters (engine-defined behavior).

---

## Gamma

A gamma distribution is another positive-valued severity model.

Common parameterization uses `shape` ($k$) and `scale` ($\theta$):

$$
X \sim \text{Gamma}(k, \theta)
$$

---

## Mixtures

A mixture model represents severity as a weighted combination of component distributions.

Conceptually, you choose a component $C$ with probability $w_c$ and then sample $X \mid C$.

**Important:** mixture support is engine-defined.

Reference engine limitation:

- The current reference engine’s `mixture` severity uses only the first component and ignores weights.

See: [Engine capabilities: Supported models](../Engine/Capabilities/Supported-Models.md)
