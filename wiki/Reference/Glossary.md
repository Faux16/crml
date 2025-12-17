# Glossary

## A

**Annual Loss Expectancy (ALE)**  
See [Expected Annual Loss (EAL)](#expected-annual-loss-eal)

**Asset**  
Any resource that could be affected by a cyber risk event. Examples: servers, databases, employees, applications.

**Asset Cardinality**  
The number of assets at risk in a model. For example, 500 employees or 100 servers.

## B

**Bayesian Inference**  
A statistical method that updates probability estimates as new data becomes available. Used in advanced CRML models (QBER).

## C

**Cardinality**  
See [Asset Cardinality](#asset-cardinality)

**Confidence Level**  
The probability that a value will fall within a specified range. For example, VaR 95% has a 95% confidence level.

**CRML (Cyber Risk Modeling Language)**  
An open, declarative language for expressing cyber risk models using YAML syntax.

**Cyber Risk**  
The potential for loss or harm related to technical infrastructure, use of technology, or reputation of an organization.

## D

**Distribution**  
A mathematical function that describes the probability of different outcomes. Common distributions in CRML: Poisson, Lognormal, Gamma.

## E

**EAL (Expected Annual Loss)**  
The average loss expected per year from a specific risk. Calculated as the mean of all simulated loss values.

**Event**  
A single occurrence of a risk scenario. For example, one phishing attack or one ransomware infection.

## F

**FAIR (Factor Analysis of Information Risk)**  
A quantitative risk analysis framework. CRML can model FAIR-style risks.

**Frequency**  
How often risk events occur. In CRML scenarios, frequency is a **threat-side** (threat landscape) assumption about baseline event likelihood, typically annualized.

**Frequency Model**  
The statistical distribution used to model how often events occur (e.g., Poisson, Gamma).

## G

**Gamma Distribution**  
A continuous probability distribution used for modeling frequency or severity. More flexible than Poisson or Lognormal.

## H

**Hierarchical Model**  
A statistical model with multiple levels of parameters. Used in advanced CRML models for more realistic risk modeling.

## I

**Incident**  
See [Event](#event)

## L

**Lambda (λ)**  
The rate parameter in a Poisson distribution.

In CRML scenarios, `lambda` represents **baseline threat-event frequency** (threat likelihood) for the chosen basis (e.g., events per organization-year or per asset-unit-year). Organization-specific **vulnerability likelihood** (susceptibility) is represented separately via portfolios/control assessments and is applied as mitigation (e.g., reducing effective `lambda`).

**Lognormal Distribution**  
A probability distribution where the logarithm of the variable is normally distributed. Commonly used for modeling cyber loss amounts because most losses are small, but some are very large.

**Loss**  
The financial impact of a risk event. Measured in dollars.

**Loss Exceedance Curve (LEC)**  
A graph showing the probability of losses exceeding various amounts. Similar to VaR but shows the full distribution.

## M

**MCMC (Markov Chain Monte Carlo)**  
An advanced simulation method used for Bayesian inference. Used in QBER models for hierarchical parameter estimation.

**Median**  
The middle value in a distribution. Half of values are below the median, half are above.

**Meta**  
Metadata section in a CRML model containing name, description, version, etc.

**Monte Carlo Simulation**  
A computational technique that uses random sampling to estimate outcomes. CRML uses Monte Carlo to simulate thousands of possible risk scenarios.

**Mu (μ)**  
The location parameter in a Lognormal distribution. Equal to the natural logarithm of the median loss: μ = ln(median).

## P

**Parameter**  
A value that defines a distribution. For example, lambda for Poisson, mu and sigma for Lognormal.

**Percentile**  
A value below which a given percentage of observations fall. For example, the 95th percentile (VaR 95%) is the value below which 95% of losses fall.

**Poisson Distribution**  
A discrete probability distribution that models the number of events occurring in a fixed time period. Commonly used for modeling cyber event frequency.

**Portfolio**  
A collection of related risks or assets. Portfolio-level modeling considers organization-wide risk.

## Q

**QBER (Quantified Bayesian Enterprise Risk)**  
An advanced risk modeling approach using Bayesian hierarchical models. Supported in CRML for complex scenarios.

**Quantile**  
See [Percentile](#percentile)

## R

**Risk**  
The potential for loss or harm. In CRML, risk is quantified as a combination of frequency and severity.

**Risk Metric**  
A numerical measure of risk. Examples: EAL, VaR, standard deviation.

**Run**  
A single iteration of a Monte Carlo simulation. CRML typically uses 10,000 runs for accurate results.

## S

**Scenario**  
A specific risk situation being modeled. For example, "phishing attacks on employees" or "ransomware on servers".

**Seed**  
A value used to initialize a random number generator. Using the same seed produces identical simulation results (reproducibility).

**Severity**  
The magnitude of loss when a risk event occurs.

In CRML scenarios, severity is a **threat-side impact** assumption (monetary loss per event), modeled using distributions like Lognormal or Gamma.

**Severity Model**  
The statistical distribution used to model loss amounts (e.g., Lognormal, Gamma).

**Sigma (σ)**  
The scale parameter in a Lognormal distribution. Represents the variability of losses. Higher sigma = more variable losses.

## T

**Threat**  
An external actor/event pattern represented by the scenario (industry, size, threat landscape). Threat data in CRML scenarios is captured via frequency (likelihood) and severity (impact).

**Threat Likelihood (Threat Frequency)**  
The baseline likelihood of the threat producing events for the chosen basis (commonly annualized). In CRML, this is represented by the scenario’s frequency model and parameters (e.g., Poisson `lambda`).

**Threat Impact**  
The monetary loss when a threat event occurs. In CRML, this is represented by the scenario’s severity model and parameters (e.g., Lognormal `median`/`mu`/`sigma`).

**Vulnerability Likelihood (Susceptibility)**  
The organization-specific likelihood that a threat event succeeds/causes loss given posture (controls, coverage, reliability). In CRML, this is represented via portfolio/control assessment control posture and is applied as mitigation (primarily reducing effective frequency in the reference engine).

**Vulnerability Impact**  
How large an event’s impact would be due to organization-specific weaknesses. The reference CRML approach does not model vulnerability impact separately; impact is modeled on the threat side via scenario severity.

**Simulation**  
The process of running a Monte Carlo model to generate risk estimates.

**Standard Deviation**  
A measure of variability in a distribution. Shows how spread out values are from the mean.

## T

**Tail Risk**  
The risk of extreme, rare events. Represented by high percentiles like VaR 99% or VaR 99.9%.

## V

**Value at Risk (VaR)**  
A risk metric showing the maximum loss expected at a given confidence level. For example, VaR 95% = $500K means there's a 95% chance annual losses will be below $500K.

**VaR 95%**  
Value at Risk at the 95th percentile. In 95% of years, losses will be below this amount. Only 1 in 20 years will exceed it.

**VaR 99%**  
Value at Risk at the 99th percentile. In 99% of years, losses will be below this amount. Only 1 in 100 years will exceed it.

**VaR 99.9%**  
Value at Risk at the 99.9th percentile. Extreme worst-case scenario. Only 1 in 1000 years will exceed it.

## Y

**YAML (YAML Ain't Markup Language)**  
A human-readable data serialization format. CRML models are written in YAML.

---

## Common Formulas

### Lognormal Median
```
median = e^μ
μ = ln(median)
```

### Expected Annual Loss (EAL)
```
EAL = mean(all simulated losses)
```

### Value at Risk
```
VaR_95% = 95th percentile of simulated losses
VaR_99% = 99th percentile of simulated losses
```

---

## Units

**Frequency:**
- Lambda: probability per asset per year
- Example: λ = 0.05 means 5% chance per asset per year

**Severity:**
- All loss amounts in dollars (USD)
- Mu: natural log of median loss in dollars
- Example: μ = 11.5 means median loss ≈ $100,000

**Time:**
- All models assume annual time periods
- Frequency is per year
- EAL is per year

---

## Abbreviations

- **ALE**: Annual Loss Expectancy (same as EAL)
- **CRML**: Cyber Risk Modeling Language
- **EAL**: Expected Annual Loss
- **FAIR**: Factor Analysis of Information Risk
- **LEC**: Loss Exceedance Curve
- **MCMC**: Markov Chain Monte Carlo
- **QBER**: Quantified Bayesian Enterprise Risk
- **VaR**: Value at Risk
- **YAML**: YAML Ain't Markup Language

---

## See Also

- [Writing CRML Models](../Guides/Writing-CRML) - Learn how to use these terms in practice
- [Understanding Parameters](understanding-parameters.md) - Deep dive on distributions
- [FAQ](faq.md) - Common questions about these concepts
