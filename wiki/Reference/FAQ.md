# Frequently Asked Questions

## General Questions

### What is CRML?

CRML (Cyber Risk Modeling Language) is an open, declarative language for expressing cyber risk models. It allows you to:

- Model cyber risks using statistical distributions
- Run Monte Carlo simulations
- Calculate risk metrics (EAL, VaR)
- Make data-driven security decisions

Think of it as "YAML for cyber risk" - simple, readable, and powerful.

---

### How accurate are CRML simulations?

CRML simulations are as accurate as the parameters you provide. The Monte Carlo method itself is mathematically sound and widely used in finance and insurance.

**Accuracy depends on:**
- Quality of input parameters (lambda, mu, sigma)
- Number of simulation runs (more = more accurate)
- How well your model represents reality

**Best practices:**
- Use industry data (Verizon DBIR, IBM reports)
- Calibrate from your historical incidents
- Start conservative, refine over time
- Run sensitivity analysis

---

### Do I need to be a statistician to use CRML?

No! CRML is designed for security professionals, not statisticians.

**You need to understand:**
- Basic probability (what's a 10% chance?)
- Your organization's risks
- How to read industry reports

**You don't need:**
- Advanced mathematics
- Statistical software experience
- Programming skills (though Python API is available)

The [Writing CRML guide](../Guides/Writing-CRML) explains everything step-by-step.

---

### How does CRML compare to other risk tools?

| Feature | CRML | FAIR-U | RiskLens | Spreadsheets |
|---------|------|--------|----------|--------------|
| Open Source | ✅ | ❌ | ❌ | ✅ |
| Cost | Free | Paid | Paid | Free |
| Learning Curve | Low | Medium | Medium | Low |
| Flexibility | High | Medium | Low | High |
| Statistical Rigor | High | High | High | Varies |
| Automation | ✅ | Limited | ✅ | Limited |

**CRML advantages:**
- Free and open source
- Simple YAML syntax
- Extensible and programmable
- Active development

---

## Technical Questions

### How do I choose between Poisson and Gamma for frequency?

**Use Poisson when:**
- Events are random and independent
- You know the probability per asset
- Examples: phishing, malware, random attacks

**Use Gamma when:**
- Frequency varies significantly
- Events come in clusters
- Examples: attack campaigns, seasonal patterns

**Rule of thumb:** Start with Poisson. It's simpler and works for 90% of cases.

---

### How do I choose between Lognormal and Gamma for severity?

**Use Lognormal when:**
- Most losses are small, but some are huge
- Distribution is right-skewed
- Examples: data breaches, ransomware, most cyber losses

**Use Gamma when:**
- Losses are more symmetric
- You have specific shape/scale parameters
- Less common in cyber risk

**Rule of thumb:** Use Lognormal for cyber risk. It matches real-world loss distributions.

---

### What if I don't have historical data?

You have several options:

**1. Use industry data:**
- Verizon DBIR (Data Breach Investigations Report)
- IBM Cost of Data Breach Report
- Sophos State of Ransomware
- Ponemon Institute studies

**2. Expert estimates:**
- Ask your security team
- Use conservative estimates
- Document assumptions

**3. Start simple:**
```yaml
# Conservative phishing model
frequency:
  lambda: 0.05  # 5% (lower than industry average)
severity:
  mu: 10.0      # ~$22K (modest loss)
  sigma: 1.0    # Moderate variability
```

**4. Calibrate over time:**
- Start with estimates
- Track actual incidents
- Refine parameters quarterly

---

### How many simulation runs should I use?

**Quick testing:** 1,000 runs (fast, less accurate)  
**Standard analysis:** 10,000 runs (recommended)  
**High precision:** 100,000 runs (slow, very accurate)

**Rule of thumb:** Use 10,000 runs. It's the sweet spot between speed and accuracy.

---

### What does "mu" mean in lognormal distribution?

`mu` is the natural logarithm of the median loss.

**Quick formula:**
```
median_loss = e^mu
mu = ln(median_loss)
```

**Examples:**
- mu = 10.0 → ~$22K median loss
- mu = 11.5 → ~$100K median loss
- mu = 13.5 → ~$700K median loss

**Tip:** Use an online calculator or: `python -c "import math; print(math.exp(11.5))"`

---

### Can I model multiple risk scenarios in one file?

By design, **each CRML file represents one scenario**.

If you want to model multiple scenarios (a portfolio), use **separate files** and aggregate results in whatever runtime/tooling you use.

```text
phishing-risk.yaml
ransomware-risk.yaml
data-breach-risk.yaml
```

If you also want to **describe and validate how those scenario files relate to each other** (weights, correlations, conditional dependencies), use a separate **CRML Portfolio** document.

```yaml
crml_portfolio: "1.0"
meta: {name: "Cyber risk portfolio"}
portfolio:
  semantics: {method: mixture}
  scenarios:
    - id: phishing
      path: phishing-risk.yaml
      weight: 0.7
    - id: ransomware
      path: ransomware-risk.yaml
      weight: 0.3
  relationships:
    - type: correlation
      between: [phishing, ransomware]
      value: 0.2
```

Within a single scenario file, you can still model **multiple assets**. CRML supports per-asset frequency and severity via `model.frequency.models` and `model.severity.models`.

```yaml
crml: "1.1"
meta: {name: "Single scenario with multiple assets"}

model:
  assets:
    - name: "Employee_Laptops"
      cardinality: 100
    - name: "Production_Database"
      cardinality: 1

  frequency:
    models:
      - asset: "Employee_Laptops"
        model: poisson
        parameters: {lambda: 0.10}
      - asset: "Production_Database"
        model: poisson
        parameters: {lambda: 0.02}

  severity:
    models:
      - asset: "Employee_Laptops"
        model: lognormal
        parameters: {median: "20 000", currency: USD, sigma: 1.0}
      - asset: "Production_Database"
        model: lognormal
        parameters: {median: "500 000", currency: USD, sigma: 1.8}
```

---

## Practical Questions

### How do I present CRML results to executives?

**Focus on three numbers:**

1. **EAL (Expected Annual Loss)** - "We expect to lose $X per year on average"
2. **VaR 95%** - "In 95% of years, losses will be below $Y"
3. **VaR 99%** - "Only 1 in 100 years will exceed $Z"

**Example executive summary:**
```
Phishing Risk Assessment

Expected Annual Loss: $220,000
- Budget this amount for phishing-related costs

95% Confidence Level: $450,000
- Losses will likely stay below this

Worst-Case Scenario (99%): $650,000
- Ensure insurance covers at least this amount

Recommendation: Invest $50K in MFA to reduce EAL by 60%
```

**Tip:** Use CRML Studio's charts for visual impact!

---

### Can I use CRML for compliance (SOC 2, ISO 27001)?

Yes! CRML helps with:

**SOC 2:**
- Risk assessment documentation
- Quantitative risk analysis
- Control effectiveness measurement

**ISO 27001:**
- Annex A risk treatment
- Risk assessment methodology
- Continuous monitoring

**PCI DSS:**
- Annual risk assessment
- Compensating controls analysis

**Tip:** Export results to JSON and include in compliance documentation.

---

### How do I justify security budget with CRML?

**1. Calculate current risk:**
```bash
crml simulate current-state.yaml
# EAL: $500K
```

**2. Model with proposed control:**
```yaml
# Reduce lambda by 70% with MFA
frequency:
  lambda: 0.03  # Down from 0.10
```

**3. Calculate risk reduction:**
```bash
crml simulate with-mfa.yaml
# EAL: $150K
```

**4. Show ROI:**
```
Risk Reduction: $500K - $150K = $350K/year
Control Cost: $50K/year
ROI: 7x return on investment
Payback Period: 2 months
```

---

### Can I integrate CRML with my SIEM/GRC tool?

Yes! CRML has several integration options:

**1. JSON output:**
```bash
crml simulate model.yaml --format json > results.json
```

**2. Python API:**
```python
from crml_engine.runtime import run_simulation

result = run_simulation("model.yaml", n_runs=10000)
payload = result.model_dump()

# Send to your GRC platform
grc_api.upload_risk_assessment(payload)
```

**3. REST API** (via CRML Studio):
```bash
curl -X POST http://localhost:3000/api/simulate \
  -H "Content-Type: application/json" \
  -d @model.yaml
```

**4. Scheduled updates:**
```bash
# Cron job to update risk dashboard
0 0 * * * crml simulate model.yaml --format json | \
  curl -X POST https://dashboard.example.com/api/risk
```

---

## Troubleshooting

### My simulation results seem wrong

**Check these common issues:**

1. **Lambda too high/low:**
   - Lambda = 0.10 means 10% per asset per year
   - Not 10 events per year!

2. **Mu confusion:**
   - Mu is ln(median), not the median itself
   - Use: `mu = ln(desired_median_loss)`

3. **Cardinality:**
   - Set to number of assets at risk
   - Not total employees/servers

4. **Units:**
   - All losses in dollars
   - All frequencies per year

**Debug tip:** Start with known examples from the docs and modify incrementally.

---

### Validation errors

**Common YAML errors:**

```yaml
# ❌ Wrong: tabs instead of spaces
model:
	frequency:  # Tab character

# ✅ Correct: spaces
model:
  frequency:  # 2 spaces
```

```yaml
# ❌ Wrong: missing quotes
meta:
  name: my-model  # Should be quoted if contains hyphens

# ✅ Correct:
meta:
  name: "my-model"
```

**Use the validator:**
```bash
crml validate model.yaml
```

---

### Performance issues

**Simulation too slow?**

1. **Reduce runs temporarily:**
   ```bash
   crml simulate model.yaml --runs 1000
   ```

2. **Check cardinality:**
   - Very large cardinality (>100,000) can be slow
   - Consider portfolio-level modeling instead

3. **Use JSON output:**
   - Faster than formatted text
   ```bash
   crml simulate model.yaml --format json
   ```

---

## Advanced Questions

### Can I model correlated risks?

CRML 1.1 includes an optional dependency block (copula-style) for engines that implement it.

The reference engine (`crml_engine`) currently supports a simpler engine-specific mechanism:

```yaml
model:
  correlations:
    - assets: ["ransomware", "data_breach"]
      value: 0.7
```

This affects how the reference engine generates correlated randomness across scenarios.

---

### Can I model time-varying risk?

Not directly, but you can:

**1. Model different time periods:**
```yaml
# Q4 (higher risk)
frequency:
  lambda: 0.15  # 50% increase
```

**2. Run multiple scenarios:**
```bash
crml simulate q1-model.yaml
crml simulate q2-model.yaml
crml simulate q3-model.yaml
crml simulate q4-model.yaml
```

**3. Use Python for trends:**
```python
# Model increasing trend
lambdas = [0.05, 0.06, 0.07, 0.08]  # Growing risk
for i, lam in enumerate(lambdas):
    model.update_parameter("frequency.lambda", lam)
    results = model.simulate()
    print(f"Q{i+1} EAL: ${results.eal}")
```

---

### How do I model security controls?

**Method 1: Adjust parameters**
```yaml
# Before MFA
frequency:
  lambda: 0.10  # 10% phishing success

# After MFA (85% reduction)
frequency:
  lambda: 0.015  # 1.5% success rate
```

**Method 2: Separate models**
```
baseline-risk.yaml      # No controls
with-mfa.yaml          # With MFA
with-mfa-and-edr.yaml  # Multiple controls
```

**Method 3: Python calculation**
```python
baseline = CRMLModel("baseline.yaml")
control_effectiveness = 0.85  # 85% reduction

reduced_lambda = baseline.lambda * (1 - control_effectiveness)
```

---

## Still Have Questions?

- 📖 [Read the full documentation](index.md)
- 💬 [Ask on GitHub Discussions](https://github.com/Faux16/crml/discussions)
- 🐛 [Report bugs](https://github.com/Faux16/crml/issues)
- 📧 [Email us](mailto:research@zeron.one)

**Can't find your answer?** [Open a GitHub issue](https://github.com/Faux16/crml/issues/new) and we'll add it to this FAQ!
