# Understanding CRML Parameters

A practical guide to choosing the right parameters for your cyber risk models.

---

## Simulation Parameters

### Number of Iterations

**What it is:** How many times the simulation runs to estimate your risk.

**How to choose:**

| Iterations | Use Case | Accuracy | Speed |
|------------|----------|----------|-------|
| 100-1,000 | Quick testing, prototyping | Low | Very Fast (< 1s) |
| 5,000-10,000 | Standard analysis, reporting | Good | Fast (2-5s) |
| 50,000-100,000 | High-stakes decisions, compliance | Excellent | Slower (10-30s) |

**Rule of thumb:** Start with 10,000 for most use cases. Increase if:
- Making million-dollar decisions
- Presenting to executives or board
- Need regulatory compliance documentation

**Why it matters:** More iterations = more stable, reliable results. Like flipping a coin - 10 flips might give you 7 heads, but 10,000 flips will be very close to 50/50.

### Random Seed

**What it is:** A number that makes your simulation reproducible.

**When to use:**
- ✅ **Testing**: Use the same seed (e.g., 42) to verify code changes don't affect results
- ✅ **Documentation**: Include seed in reports so others can reproduce your analysis
- ✅ **Debugging**: Use a seed to get consistent results while troubleshooting
- ❌ **Production**: Leave empty for different results each time (more realistic)

**Example:**
```yaml
# Reproducible (always same results)
pipeline:
  simulation:
    monte_carlo:
      runs: 10000
      random_seed: 42

# Non-reproducible (different each time)
pipeline:
  simulation:
    monte_carlo:
      runs: 10000
      # No seed specified
```

---

## Distribution Selection

### Understanding Distributions

Distributions describe **how often** (frequency) and **how bad** (severity) cyber events occur.

### Frequency Distributions

**Question:** "How many times will this happen per year?"

#### Poisson Distribution

**Use when:** Events are rare and random (most cyber risks)

**Parameters:**
- `lambda`: Average number of events per year per asset

**How to choose lambda:**

| Lambda | Meaning | Example |
|--------|---------|---------|
| 0.01 | 1% chance per asset per year | Zero-day exploits |
| 0.05 | 5% chance per asset per year | Data breaches |
| 0.1 | 10% chance per asset per year | Phishing incidents |
| 0.5 | 50% chance per asset per year | Failed login attempts |
| 1.0 | Expected once per asset per year | Malware detections |

**Real-world example:**
```yaml
# Ransomware scenario
# Industry data: ~8% of organizations hit per year
# You have 500 critical systems
frequency:
  model: poisson
  parameters:
    lambda: 0.08  # 8% per system = ~40 expected incidents/year across all systems
```

**Where to get lambda values:**
- Industry reports (Verizon DBIR, IBM Cost of Data Breach)
- Your own historical incident data
- Threat intelligence feeds
- Peer benchmarking

#### Gamma Distribution

**Use when:** Event frequency varies over time or between assets

**Parameters:**
- `shape`: How variable the rate is
- `scale`: Average rate

**When to use:** Advanced modeling when Poisson is too simple (e.g., seasonal attacks, varying asset criticality)

---

### Severity Distributions

**Question:** "When it happens, how much will it cost?"

#### Lognormal Distribution

**Use when:** Losses are typically small but can be extremely large (most cyber losses)

**Parameters:**
- `median`: The typical (median) loss amount in real currency. Accepts numbers or strings with spaces (e.g., `"100 000"`).
- `currency`: The currency code for the median value (e.g., USD, EUR)
- `sigma`: Controls the variability (how spread out losses are)
- `mu`: Alternative to median - log-space mean (advanced users only)
- `single_losses`: List of observed or estimated single-event loss amounts for auto-calibration (do not combine with median/mu/sigma). Each value can be a number or a string with spaces.
- `cardinality`: Number of assets of this type. Accepts numbers or strings with spaces (e.g., `"10 000"`).
- `lambda`: Poisson rate parameter. Accepts numbers or strings with spaces (e.g., `"1 200"`).
- `alpha_base`: Gamma shape parameter for hierarchical_gamma_poisson. Accepts numbers, strings with spaces, or expressions (e.g., `"1 000"`, `"CI * 2 + 1"`).
- `beta_base`: Gamma rate parameter for hierarchical_gamma_poisson. Accepts numbers or strings with spaces (e.g., `"10 000"`).

**Number Format:** Large numbers support ISO 80000-1 style space separators for readability. Both `100000` and `"100 000"` are valid.
This applies to all relevant parameters, including `median`, `cardinality`, `lambda`, `alpha_base`, `beta_base`, `shape`, `scale`, and `single_losses`. For example:

```yaml
assets:
  - name: Laptops
    cardinality: "10 000"  # 10,000 laptops
  - name: Servers
    cardinality: 500

frequency:
  model: poisson
  parameters:
    lambda: "1 200"  # 1,200 expected events

  # Hierarchical example
  model: hierarchical_gamma_poisson
  parameters:
    alpha_base: "1 000"
    beta_base: "10 000"
```

**How to choose median:**

Simply use the typical loss amount directly from industry reports, own historical loss data or expert judgement.

| Median | Use Case |
|--------|----------|
| 8 000 | Minor incidents (laptop theft) |
| "100 000" | Data breaches (small) |
| "700 000" | Ransomware (medium enterprise) |
| "9 000 000" | Major data breach (large enterprise) |

**How to choose sigma:**

| sigma | Variability | Meaning |
|-------|-------------|---------|
| 0.5 | Low | Losses are predictable, clustered around median |
| 1.0-1.5 | Medium | Typical cyber risk - some variation |
| 2.0+ | High | Extreme variation - rare catastrophic losses possible |

**Real-world example:**
```yaml
# Data breach severity
# Industry data: Median cost ~$100K, but can reach millions
severity:
  model: lognormal
  parameters:
    median: "100 000"  # $100K median (directly from IBM report)
    currency: USD      # Explicit currency
    sigma: 1.2         # Moderate variability
```

**Visual guide:**
- **Low sigma (0.5)**: 📊 Narrow bell curve - predictable losses
- **Medium sigma (1.2)**: 📊 Wider curve - some big losses possible
- **High sigma (2.0)**: 📊 Very wide - rare but catastrophic losses

**Note on `mu`:** For advanced users, you can still use `mu` (the log-space mean where `mu = ln(median)`). However, `median` is recommended because:
- It's more intuitive and human-readable
- It directly maps to industry report data
- No manual log transformation required

#### Gamma Distribution

**Use when:** Losses have a natural minimum but long tail (e.g., recovery costs)

**Parameters:**
- `shape`: Controls the distribution shape
- `scale`: Controls the average loss size

**When to use:** Alternative to lognormal when you want more control over the tail behavior

---

## Practical Workflow

### Step 1: Gather Data

**For Frequency (lambda):**
1. Check your incident logs (how many times did X happen last year?)
2. Consult industry reports (Verizon DBIR, Ponemon, etc.)
3. Ask: "Out of 100 similar assets, how many get hit per year?"

**For Severity (mu, sigma):**
1. Review past incident costs (direct + indirect)
2. Use industry benchmarks (IBM Cost of Data Breach Report)
3. Consider: downtime, recovery, legal, reputation, fines

### Step 2: Start Simple

```yaml
# Begin with a simple model
model:
  assets:
    cardinality: 100  # Number of assets you're protecting
  frequency:
    model: poisson
    parameters:
      lambda: 0.05  # 5% chance per asset (conservative estimate)
  severity:
    model: lognormal
    parameters:
      median: "100 000"  # $100K median loss
      currency: USD
      sigma: 1.2         # Moderate variability
```
      sigma: 1.2 # Moderate variability
```

### Step 3: Calibrate

Run the simulation and check if results make sense:

```
Expected Annual Loss: $500K
VaR 95%: $1.2M
```

**Ask yourself:**
- Does $500K/year seem reasonable for my organization?
- Would I be comfortable explaining this to my CISO?
- Does it align with our cyber insurance premium?

### Step 4: Adjust

If results seem off:

**Too high?**
- Reduce `lambda` (events are rarer than you thought)
- Reduce `median` (losses are smaller than you thought)

**Too low?**
- Increase `lambda` (events are more common)
- Increase `median` (losses are larger)
- Increase `sigma` (more variability, captures rare big losses)

---

## Common Scenarios

### Scenario 1: Ransomware Risk

**Context:** Enterprise with 500 critical servers

```yaml
model:
  assets:
    cardinality: 500
  frequency:
    model: poisson
    parameters:
      lambda: 0.08  # 8% annual probability (industry average)
  severity:
    model: lognormal
    parameters:
      median: "700 000"  # $700K median (ransom + downtime + recovery)
      currency: USD
      sigma: 1.8         # High variability (some pay $50K, others $5M)
```

**Why these values?**
- Lambda: Sophos reports ~66% of orgs hit in 2 years ≈ 33%/year, but per-server is lower
- Median: Average ransomware cost is $700K-$1.4M (Sophos, 2023)
- Sigma: High because costs vary wildly based on negotiation, backups, etc.

### Scenario 2: Data Breach (PII)

**Context:** 50 databases containing customer PII

```yaml
model:
  assets:
    cardinality: 50
  frequency:
    model: poisson
    parameters:
      lambda: 0.05  # 5% per database per year
  severity:
    model: lognormal
    parameters:
      median: "100 000"  # $100K median
      currency: USD
      sigma: 1.2         # Moderate variability
```

**Why these values?**
- Lambda: IBM reports 1 in 20 orgs have breach per year ≈ 5%
- Median: IBM Cost of Data Breach 2023: $4.45M average, but varies by size
- Sigma: Moderate because costs are somewhat predictable (per-record costs)

### Scenario 3: Phishing Incidents

**Context:** 1000 employees, measuring credential compromise

```yaml
model:
  assets:
    cardinality: 1000  # employees
  frequency:
    model: poisson
    parameters:
      lambda: 0.2  # 20% of employees click phishing per year
  severity:
    model: lognormal
    parameters:
      median: "8 000"  # $8K median (mostly time to remediate)
      currency: USD
      sigma: 1.5       # Some lead to major breaches
```

**Why these values?**
- Lambda: Industry average click rate is 10-30%
- Median: Most phishing is caught quickly, low cost
- Sigma: But some lead to major breaches, so high variability

---

## Data Sources

### Industry Reports (Free)
- **Verizon DBIR**: Breach frequency by industry
- **IBM Cost of Data Breach**: Average costs by breach type
- **Ponemon Institute**: Various cost studies
- **SANS Institute**: Incident statistics

### Threat Intelligence
- **MITRE ATT&CK**: Technique frequency
- **CISA Alerts**: Current threat landscape
- **Your SIEM/EDR**: Historical incident data

### Insurance Data
- **Cyber insurance applications**: Often require incident history
- **Industry loss data**: Some insurers publish aggregated data

---

## Quick Reference Card

**Starting point for common scenarios:**

| Risk Type | Lambda | Median | Sigma | Rationale |
|-----------|--------|--------|-------|-----------|
| Ransomware (Enterprise) | 0.08 | $700,000 | 1.8 | Industry avg: 8%, $700K median, high variance |
| Data Breach (SMB) | 0.05 | $100,000 | 1.2 | 5% annual, $100K median, moderate variance |
| Phishing (per employee) | 0.2 | $8,000 | 1.5 | 20% click rate, $8K median, some escalate |
| DDoS Attack | 0.15 | $35,000 | 1.0 | 15% annual, $35K median, predictable costs |
| Insider Threat | 0.02 | $1,200,000 | 2.0 | Rare (2%), $1.2M median, highly variable |

**Simulation iterations:**
- **Quick test**: 1,000
- **Standard analysis**: 10,000
- **Board presentation**: 50,000+

---

## Next Steps

1. **Start with examples**: Use the pre-built models in the simulation page
2. **Modify one parameter at a time**: See how it affects results
3. **Compare to your budget**: Does the EAL match your cyber spend?
4. **Iterate**: Refine based on your organization's data

**Remember:** All models are wrong, but some are useful. Start simple, validate with stakeholders, and refine over time.
