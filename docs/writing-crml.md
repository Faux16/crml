# Writing CRML Models: A Practical Guide

This guide will teach you how to write CRML models from scratch, step by step.

## Table of Contents

1. [Basic Structure](#basic-structure)
2. [Step-by-Step Tutorial](#step-by-step-tutorial)
3. [Common Patterns](#common-patterns)
4. [Tips & Best Practices](#tips-best-practices)

---

## Basic Structure

Every CRML model has three main sections:

```yaml
crml: "1.1"              # Version (required)
meta:                    # Metadata (optional but recommended)
  name: "my-model"
  description: "What this models"
model:                   # The actual risk model (required)
  # Your model definition goes here
```

---

## Step-by-Step Tutorial

### Step 1: Start with Metadata

Always start by describing what you're modeling:

```yaml
crml: "1.1"
meta:
  name: "phishing-risk"
  description: "Phishing attack risk for email users"
  version: "1.1"
  author: "Security Team"
  tags:
    - phishing
    - email
```

**Why?** Good metadata helps you and others understand the model later.

---

### Step 2: Define Your Assets

What are you protecting? How many of them?

```yaml
model:
  assets:
    cardinality: 500  # 500 employees with email
```

**Common asset types:**
- Employees (for phishing, insider threats)
- Servers (for ransomware, outages)
- Databases (for data breaches)
- Applications (for vulnerabilities)

---

### Step 3: Model Event Frequency

How often do bad things happen?

#### **Option A: Poisson (Most Common)**

Use when events are random and independent:

```yaml
  frequency:
    model: poisson
    parameters:
      lambda: 0.05  # 5% chance per asset per year
```

**When to use Poisson:**
- Random attacks (phishing, malware)
- Independent events
- You know the probability per asset

**Choosing lambda:**
- 0.01 = 1% (very rare, like zero-days)
- 0.05 = 5% (data breaches)
- 0.10 = 10% (phishing clicks)
- 0.50 = 50% (common issues)

#### **Option B: Gamma**

Use for more variable frequencies:

```yaml
  frequency:
    model: gamma
    parameters:
      shape: 2.0
      scale: 0.5
```

**When to use Gamma:**
- Frequency varies significantly
- Clustered events (attack campaigns)

---

### Step 4: Model Loss Severity

When an event happens, how bad is it?

#### **Option A: Lognormal (Most Common)**

Use when most losses are small, but some are huge:

```yaml
  severity:
    model: lognormal
    parameters:
      median: "100 000"  # $100K median loss
      currency: USD      # Explicit currency
      sigma: 1.2         # Moderate variability
```

**Choosing median (typical loss):**
- median: "8 000"     → ~$8K (minor incidents)
- median: "100 000"   → ~$100K (data breaches)
- median: "700 000"   → ~$700K (ransomware)
- median: "9 000 000" → ~$9M (major breaches)

**Choosing sigma (variability):**
- 0.5 = Low variability (predictable losses)
- 1.0 = Moderate variability
- 1.5 = High variability
- 2.0+ = Extreme variability (some losses 100x others)

**Note:** You can also use `mu` (log-space mean) for advanced use, but `median` is recommended as it's more intuitive and directly corresponds to real-world data.

#### **Option B: Gamma**

Use for more symmetric loss distributions:

```yaml
  severity:
    model: gamma
    parameters:
      shape: 3.0
      scale: 50000  # Average loss around $150K
```

---

### Step 5: Put It All Together

Here's a complete phishing model:

```yaml
crml: "1.1"
meta:
  name: "phishing-risk"
  description: "Annual phishing risk for 500 employees"
  
model:
  assets:
    cardinality: 500  # 500 employees
    
  frequency:
    model: poisson
    parameters:
      lambda: 0.10  # 10% click rate (industry average)
      
  severity:
    model: lognormal
    parameters:
      median: "22 000"  # $22K median loss
      currency: USD
      sigma: 1.5        # High variability
```

**What this means:**
- 500 employees, each has 10% chance of clicking phishing link per year
- Expected ~50 incidents per year
- Each incident costs ~$22K on average (credential reset, investigation, etc.)
- Some incidents much more expensive (wire fraud, data breach)

---

## Common Patterns

### Pattern 1: Simple Per-Asset Risk

**Use case:** Each asset has independent risk

```yaml
model:
  assets:
    cardinality: 100  # 100 servers
  frequency:
    model: poisson
    parameters:
      lambda: 0.02  # 2% per server
  severity:
    model: lognormal
    parameters:
      median: "162 755"  # ~$163K median loss
      currency: USD
      sigma: 1.0
```

---

### Pattern 2: Portfolio-Level Risk

**Use case:** Risk affects the whole organization, not individual assets

```yaml
model:
  frequency:
    model: poisson
    scope: portfolio  # Organization-wide
    parameters:
      lambda: 1.5  # 1-2 events per year total
  severity:
    model: lognormal
    parameters:
      median: "1 200 000"  # ~$1.2M median
      currency: USD
      sigma: 2.0           # High variability
```

**When to use:**
- Ransomware (hits whole org)
- Cloud outages
- Vendor breaches

---

### Pattern 3: Mixture Models (Advanced)

**Use case:** Different types of losses

```yaml
model:
  severity:
    model: mixture
    components:
      - lognormal:  # 80% are small losses
          weight: 0.8
          median: "22 026"    # ~$22K
          currency: USD
          sigma: 0.8
      - lognormal:  # 20% are catastrophic
          weight: 0.2
          median: "3 269 017"  # ~$3.3M
          currency: USD
          sigma: 1.5
```

---

## Tips & Best Practices

### ✅ DO:

1. **Start simple** - Begin with Poisson + Lognormal
2. **Use industry data** - Check Verizon DBIR, IBM reports
3. **Document your assumptions** - Add comments explaining parameter choices
4. **Test with different values** - Use the playground to experiment
5. **Compare to reality** - Does the output match your experience?

### ❌ DON'T:

1. **Don't guess wildly** - Use data or expert estimates
2. **Don't over-complicate** - Simple models are often better
3. **Don't forget units** - Is lambda per year? Per month?
4. **Don't ignore validation** - Always validate your YAML

---

## Real-World Examples

### Example 1: Data Breach

```yaml
crml: "1.1"
meta:
  name: "data-breach-simple"
  description: "Customer database breach risk"
  
model:
  assets:
    cardinality: 50  # 50 databases
  frequency:
    model: poisson
    parameters:
      lambda: 0.05  # Verizon DBIR: ~5% annual
  severity:
    model: lognormal
    parameters:
      median: "100 000"  # IBM: $100K median
      currency: USD
      sigma: 1.2
```

**Data sources:**
- Lambda: Verizon DBIR 2023
- Median: IBM Cost of Data Breach Report 2023

---

### Example 2: Ransomware

```yaml
crml: "1.1"
meta:
  name: "ransomware-scenario"
  description: "Enterprise ransomware risk"
  
model:
  assets:
    cardinality: 500  # 500 critical servers
  frequency:
    model: poisson
    parameters:
      lambda: 0.08  # Sophos: 8% hit rate
  severity:
    model: lognormal
    parameters:
      median: "700 000"  # ~$700K (ransom + downtime)
      currency: USD
      sigma: 1.8         # High variability
```

**Data sources:**
- Lambda: Sophos State of Ransomware 2023
- Median: Coveware Ransomware Reports

---

### Example 3: Cloud Outage

```yaml
crml: "1.1"
meta:
  name: "cloud-outage"
  description: "SaaS provider outage impact"
  
model:
  frequency:
    model: poisson
    scope: portfolio  # Affects whole org
    parameters:
      lambda: 2.0  # 2 outages per year
  severity:
    model: lognormal
    parameters:
      median: "162 755"  # ~$163K per outage
      currency: USD
      sigma: 1.0         # Moderate variability
```

---

## Parameter Selection Cheat Sheet

### Frequency (Lambda for Poisson)

| Risk Type | Typical Lambda | Source |
|-----------|---------------|--------|
| Zero-day exploit | 0.001 - 0.01 | NIST NVD |
| Data breach | 0.03 - 0.07 | Verizon DBIR |
| Ransomware | 0.05 - 0.10 | Sophos |
| Phishing success | 0.08 - 0.15 | KnowBe4 |
| Insider threat | 0.02 - 0.05 | Ponemon |

### Severity (Median for Lognormal)

| Loss Amount | Median Value | Use Case |
|-------------|--------------|----------|
| ~$5K | 5000 | Minor incidents |
| ~$20K | 20000 | Phishing, small breaches |
| ~$100K | 100000 | Data breaches |
| ~$500K | 500000 | Ransomware |
| ~$2M | 2000000 | Major breaches |
| ~$10M | 10000000 | Catastrophic events |

**Note:** Use `median` for the median loss directly - no calculation needed! For advanced users, `mu = ln(median)`.

---

## Next Steps

1. **Try the examples** - Load them in the playground
2. **Modify parameters** - See how results change
3. **Build your own** - Start with your organization's risks
4. **Read the spec** - For advanced features
5. **Check the API docs** - For programmatic use

---

## Getting Help

- **Playground**: Try examples interactively
- **Validator**: Check your YAML syntax
- **Examples**: Browse pre-built models
- **Understanding Parameters**: Deep dive on distributions
- **GitHub Issues**: Ask questions, report bugs

---

## Quick Reference Card

```yaml
# Minimal CRML model
crml: "1.1"
meta:
  name: "my-model"
model:
  assets:
    cardinality: N  # Number of assets
  frequency:
    model: poisson
    parameters:
      lambda: X  # Probability per asset
  severity:
    model: lognormal
    parameters:
      median: Y    # Median loss in dollars (intuitive!)
      currency: USD
      sigma: Z     # Variability
```

**Remember:**
- Lambda = probability per asset per year
- Median = typical loss amount (directly in currency)
- Sigma = how variable losses are
- Currency = explicit currency declaration

Happy modeling! 🚀
