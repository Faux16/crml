# Deep Math in CRML

CRML supports advanced mathematical constructs to model cyber risk with high fidelity. This section details the core mathematical models and algorithms used.

## 1. Frequency Models

CRML allows for flexible modeling of event frequency, ranging from simple Poisson processes to complex hierarchical Bayesian models.

### Poisson Distribution
The standard model for count data, where events occur independently at a constant average rate $\lambda$.

$$ P(k; \lambda) = \frac{\lambda^k e^{-\lambda}}{k!} $$

### Hierarchical Gamma-Poisson
A Bayesian approach where the rate $\lambda$ itself is a random variable following a Gamma distribution. This allows for modeling overdispersion and parameter uncertainty.

$$ \lambda \sim \text{Gamma}(\alpha, \beta) $$
$$ k \sim \text{Poisson}(\lambda) $$

This is particularly useful in the **QBER** framework where $\alpha$ and $\beta$ can be derived from asset criticality or other covariates.

## 2. Severity Models

Severity (loss magnitude) is often heavy-tailed in cyber risk. CRML supports mixture models to capture different loss regimes.

### Mixture Models
A weighted combination of multiple probability distributions.

$$ f(x) = \sum_{i=1}^n w_i f_i(x) $$

Common components include:
- **Lognormal**: For standard operational losses.
- **Gamma**: For losses with specific shape/scale characteristics.
- **Pareto / GPD**: For extreme tail events (though often approximated by heavy-tailed Lognormal in practice).

## 3. Dependency Modeling

Cyber risks are rarely independent. CRML uses Copulas to model the correlation structure between different risk factors or assets without constraining their marginal distributions.

### Gaussian Copula
The Gaussian Copula imposes a correlation structure determined by a correlation matrix $\Sigma$ (or $\rho$).

$$ C(u_1, \dots, u_d) = \Phi_\Sigma(\Phi^{-1}(u_1), \dots, \Phi^{-1}(u_d)) $$

Where $\Phi^{-1}$ is the inverse cumulative distribution function of the standard normal distribution. This allows for modeling complex dependencies like:
- Common mode failures (e.g., cloud provider outage).
- Correlated attack vectors.

## 4. Simulation Engines

CRML specifications are executable via different simulation engines.

### Monte Carlo Simulation
The standard approach for risk quantification. It involves sampling from the defined distributions (frequency, severity, dependency) tens of thousands of times to build an aggregate loss distribution.

### Markov Chain Monte Carlo (MCMC)
Used for Bayesian inference, particularly when updating beliefs based on observed data (e.g., telemetry). CRML supports algorithms like **Metropolis-Hastings** to sample from the posterior distribution of parameters.

$$ P(\theta | D) \propto P(D | \theta) P(\theta) $$

This allows the model to "learn" from data, adjusting parameters like attack rates or control effectiveness dynamically.

## 5. Temporal Modeling

CRML supports defining time horizons (e.g., "24m" for 24 months) and granularity. This is crucial for:
- **Aggregation**: How losses accumulate over time.
- **Trend Analysis**: Modeling changing threat landscapes using regression or time-series models (e.g., Ridge Regression on temporal inputs).