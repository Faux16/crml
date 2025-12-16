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
    - name: employeeWithEmail
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

Use when events are random and independent. 

For a single asset type:

```yaml
  frequency:
    model: poisson
    parameters:
      lambda: 0.05  # 5% chance per asset per year
```

For multiple asset types, use per-asset frequency models:

```yaml
  assets:
    - name: laptop
      cardinality: 100
    - name: server
      cardinality: 50
  frequency:
    scope: asset
    models:
      - asset: laptop
        model: poisson
        parameters:
          lambda: 0.02
      - asset: server
        model: poisson
        parameters:
          lambda: 0.05
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

##### **Median vs Mu: Which Should You Use?**

> [!TIP]
> **Always use `median` instead of `mu`** - it's more intuitive and matches how loss data is reported.

CRML supports two ways to parameterize lognormal distributions:

**✅ RECOMMENDED: Use `median`**
```yaml
parameters:
  median: "100 000"  # Direct median loss value
  currency: USD
  sigma: 1.2
```

**Why median is better:**
- 📊 **Matches real data** - Breach reports give median costs, not log-space parameters
- 👥 **Human-readable** - Anyone can understand "$100K median loss"
- ✅ **Audit-friendly** - Reviewers can verify the number makes sense
- 🎯 **No math needed** - Just use the value from your data source

**❌ ADVANCED: Use `mu` (not recommended)**
```yaml
parameters:
  mu: 11.513  # ln(100000) - requires calculation
  sigma: 1.2
```

**When to use mu:**
- You're working with legacy models that use mu
- You have log-space parameters from statistical software
- You're implementing academic research that specifies mu

**Important:** You cannot use both `median` and `mu` in the same model. The validator will reject it.

##### **Multi-Currency Support**

CRML has first-class support for multi-currency models. This is essential when:
- Combining data from different regions (EU fines in EUR, US fines in USD)
- Modeling multinational organizations
- Using industry reports in different currencies

**Example: Multi-Currency Model**
```yaml
severity:
---

## Security Control Effectiveness

**New in CRML 1.1:** Model how security controls reduce cyber risk.

### Why Model Controls?

Security controls (email filtering, EDR, MFA, backups) reduce the likelihood and impact of cyber incidents. CRML allows you to:

- **Quantify control effectiveness** - See exact risk reduction
- **Optimize security spend** - Identify highest-impact controls
- **Model defense-in-depth** - Layer multiple controls realistically

### Basic Control Example

```yaml
model:
  frequency:
    model: poisson
    parameters:
      lambda: 0.15  # 15% baseline probability
  
  controls:
    layers:
      - name: "email_security"
        controls:
          - id: "email_filtering"
            type: "preventive"
            effectiveness: 0.90  # Blocks 90% of attacks
            coverage: 1.0        # Covers all users
            reliability: 0.95    # 95% uptime
```

**Result:** Risk reduced from 15% to ~1.5% (90% reduction)

### Control Parameters

#### Required

- **`id`**: Unique identifier (e.g., `"email_filtering"`, `"edr"`)
- **`type`**: Control category
  - `preventive` - Stops attacks before they occur
  - `detective` - Identifies attacks in progress
  - `recovery` - Restores after incidents
  - `corrective`, `deterrent`, `compensating`
- **`effectiveness`** (0-1): How well it works when functioning
  - `0.95-1.0` - Highly effective (immutable backups)
  - `0.80-0.95` - Very effective (MFA, EDR, email filtering)
  - `0.60-0.80` - Moderately effective (security awareness)

#### Optional

- **`coverage`** (0-1, default 1.0): What % of assets it covers
- **`reliability`** (0-1, default 1.0): How reliably it functions (uptime)
- **`cost`**: Annual cost for ROI calculations

### Defense-in-Depth Example

Layer multiple controls for maximum protection:

```yaml
controls:
  layers:
    - name: "email_security"
      controls:
        - id: "email_filtering"
          type: "preventive"
          effectiveness: 0.90
          cost: 50000
    
    - name: "endpoint_protection"
      controls:
        - id: "edr"
          type: "detective"
          effectiveness: 0.80
          coverage: 0.98
          cost: 120000
    
    - name: "backup_recovery"
      controls:
        - id: "immutable_backups"
          type: "recovery"
          effectiveness: 0.95
          cost: 75000
```

**Combined Effect:**
- Baseline: 15% probability
- After email filtering: 1.5%
- After EDR: 0.3%
- After backups: 0.015% (99% total reduction!)

### Control Dependencies

When controls overlap or may fail together:

```yaml
controls:
  layers:
    - name: "endpoint"
      controls:
        - id: "edr"
          effectiveness: 0.80
        - id: "antivirus"
          effectiveness: 0.70
  
  dependencies:
    - controls: ["edr", "antivirus"]
      correlation: 0.5  # Both target endpoint threats
```

**Correlation values:**
- `0.0` - Independent
- `0.3-0.5` - Some overlap
- `0.7-1.0` - High overlap

### Interpreting Results

When you run a simulation with controls, you'll see:

```
CONTROL EFFECTIVENESS RESULTS:
Baseline Lambda (no controls):    0.150000
Effective Lambda (with controls): 0.034602
Risk Reduction:                   76.9%
```

### Best Practices

✅ **Do:**
- Use realistic effectiveness values (0.6-0.9 for most controls)
- Layer multiple control types (preventive + detective + recovery)
- Account for coverage gaps and reliability
- Include costs for ROI analysis

❌ **Don't:**
- Use unrealistically high effectiveness (>0.95 for most controls)
- Rely on a single control
- Ignore coverage and reliability factors

### Complete Example

See [ransomware-with-controls.yaml](/spec/examples/ransomware-with-controls.yaml) for a full working example with 6 layered controls.

For detailed guidance, see the [Control Effectiveness Guide](/docs/controls-guide.md).

  model: mixture
  components:
    - lognormal:  # GDPR fines in EUR
        weight: 0.3
        median: "175 000"
        currency: EUR  # Explicit EUR
        sigma: 1.8
    - lognormal:  # CCPA fines in USD
        weight: 0.7
        median: "250 000"
        currency: USD  # Explicit USD
        sigma: 1.5
```

**FX Configuration**

Create an FX config file to control currency conversion:

```yaml
# fx-config.yaml
base_currency: USD      # Internal simulation currency
output_currency: EUR    # Report results in EUR
rates:
  EUR: 1.16  # 1 EUR = 1.16 USD
  GBP: 1.02  # 1 GBP = 1.02 USD
  CHF: 1.09
as_of: "2025-12-15"  # For documentation
```

Then run with:
```bash
crml simulate model.yaml --fx-config fx-config.yaml
```

**Supported Currencies:**
USD, EUR, GBP, CHF, JPY, CNY, CAD, AUD, INR, BRL, PKR, MXN, KRW, SGD, HKD

**Best Practices:**
1. ✅ **Always declare currency** - Even if using USD, be explicit
2. ✅ **Use external FX config** - Keeps rates separate from model logic
3. ✅ **Document FX date** - Add `as_of` to track when rates were set
4. ✅ **Use deterministic rates** - Don't fetch live rates (breaks reproducibility)

##### **Auto-Calibration from Data**

If you have real incident cost data and want it embedded in the model for auditability, you can provide `single_losses` instead and let the engine auto-calibrate:

```yaml
  severity:
    model: lognormal
    parameters:
      currency: USD
      single_losses:
        - "25 000"
        - "18 000"
        - "45 000"
        - "32 000"
        - "21 000"
```

With `single_losses`, the engine computes $\mu = \ln(\mathrm{median}(\text{single\_losses}))$ and $\sigma = \mathrm{stddev}(\ln(\text{single\_losses}))$ (so you must not also set `median`, `mu`, or `sigma`).

##### **Choosing Parameters**

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
    - name: employee
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

**Use case:** Each asset has independent risk (multiple asset types):

```yaml
model:
  assets:
    - name: laptop
      cardinality: 100
    - name: server
      cardinality: 50
  frequency:
    scope: asset
    models:
      - asset: laptop
        model: poisson
        parameters:
          lambda: 0.02
      - asset: server
        model: poisson
        parameters:
          lambda: 0.05
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
4. **Test with different values** - Use the simulation page to experiment
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
    - name: database
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
    - name: server
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

1. **Try the examples** - Load them in the simulation page
2. **Modify parameters** - See how results change
3. **Build your own** - Start with your organization's risks
4. **Read the spec** - For advanced features
5. **Check the API docs** - For programmatic use

---

## Getting Help

- **Simulation**: Try examples interactively
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
    - name: asset
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
