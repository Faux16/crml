# Getting Started with CRML

This guide will help you install CRML and run your first cyber risk simulation.

---

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Install from PyPI

```bash
pip install crml-lang
```

### Verify Installation

```bash
crml --version
```

You should see: `CRML CLI version 1.2.0`

---

## Your First Model

Let's create a simple ransomware risk model.

### 1. Create a YAML file

Create a file named `ransomware.yaml`:

```yaml
crml: "1.1"

meta:
  name: "simple-ransomware"
  description: "Basic ransomware risk model"
  author: "Your Name"

model:
  frequency:
    model: poisson
    parameters:
      lambda: 0.12  # 12% annual probability
  
  severity:
    model: lognormal
    parameters:
      median: "500 000"  # $500K median loss
      currency: USD
      sigma: 1.5  # High variability
```

### 2. Validate the Model

```bash
crml validate ransomware.yaml
```

Expected output:
```
[OK] ransomware.yaml is a valid CRML 1.1 document.
```

### 3. Run a Simulation

```bash
crml simulate ransomware.yaml --runs 10000
```

Expected output:
```
SIMULATION RESULTS
==================
Expected Annual Loss (EAL):    $60,000
Value at Risk (95%):           $1,250,000
Value at Risk (99%):           $3,500,000
Value at Risk (99.9%):         $8,200,000
```

---

## Understanding the Results

### Expected Annual Loss (EAL)
The average loss you can expect per year. Use this for budgeting.

**Example:** EAL of $60,000 means you should budget ~$60K/year for this risk.

### Value at Risk (VaR)
The maximum loss at a given confidence level.

- **VaR 95%:** 95% of years will be below this amount (1 in 20 years exceeds)
- **VaR 99%:** 99% of years will be below this amount (1 in 100 years exceeds)
- **VaR 99.9%:** Extreme worst-case scenario (1 in 1000 years)

**Example:** VaR 99% of $3.5M means there's a 1% chance of losing more than $3.5M in a given year.

---

## Adding Security Controls

Now let's add an email filtering control to reduce risk.

Update `ransomware.yaml`:

```yaml
crml: "1.1"

meta:
  name: "ransomware-with-controls"
  description: "Ransomware risk with email filtering"

model:
  frequency:
    model: poisson
    parameters:
      lambda: 0.12  # 12% baseline probability
  
  controls:
    layers:
      - name: "email_security"
        controls:
          - id: "email_filtering"
            type: "preventive"
            effectiveness: 0.85  # Blocks 85% of attacks
            coverage: 1.0        # Covers all users
            reliability: 0.95    # 95% uptime
            cost: 50000
            currency: USD
  
  severity:
    model: lognormal
    parameters:
      median: "500 000"
      currency: USD
      sigma: 1.5
```

Run the simulation again:

```bash
crml simulate ransomware.yaml --runs 10000
```

Expected output:
```
CONTROL EFFECTIVENESS RESULTS
==============================
Baseline Lambda (no controls):    0.120000
Effective Lambda (with controls): 0.018000
Risk Reduction:                   85.0%

SIMULATION RESULTS
==================
Expected Annual Loss (EAL):    $9,000
Value at Risk (95%):           $187,500
Value at Risk (99%):           $525,000
Value at Risk (99.9%):         $1,230,000
```

**Impact:** Email filtering reduced EAL from $60K to $9K (85% reduction!)

---

## Multi-Currency Support

Model risks in different currencies:

```yaml
model:
  severity:
    model: mixture
    components:
      - lognormal:  # GDPR fines in EUR
          weight: 0.3
          median: "175 000"
          currency: EUR
          sigma: 1.8
      
      - lognormal:  # CCPA fines in USD
          weight: 0.7
          median: "250 000"
          currency: USD
          sigma: 1.5
```

Specify output currency:

```bash
crml simulate model.yaml --output-currency EUR
```

---

## Auto-Calibration from Data

Have historical loss data? Let CRML calibrate parameters automatically:

```yaml
data:
  sources:
    - type: "inline"
      single_losses:
        - "125 000"
        - "450 000"
        - "89 000"
        - "1 200 000"
        - "67 000"
      currency: USD

model:
  severity:
    model: lognormal
    parameters:
      calibrate_from: "single_losses"
      # CRML will calculate median and sigma automatically
```

---

## Next Steps

- **[Control Effectiveness Guide](Control-Effectiveness)** - Learn advanced control modeling
- **[Examples](Examples)** - See real-world risk models
- **[Writing CRML Models](Writing-CRML-Models)** - Complete modeling guide
- **[API Reference](API-Reference)** - Use CRML in Python code

---

## Common Issues

### "Command not found: crml"

Make sure Python's bin directory is in your PATH:

```bash
# macOS/Linux
export PATH="$PATH:$HOME/.local/bin"

# Or use python -m
python3 -m crml.cli validate model.yaml
```

### "Invalid CRML document"

Check that:
1. YAML syntax is correct (use a YAML validator)
2. `crml: "1.1"` is specified at the top
3. All required fields are present
4. Parameter values are in valid ranges

### "ModuleNotFoundError"

Reinstall CRML:

```bash
pip uninstall crml-lang
pip install crml-lang
```

---

## Getting Help

- **Documentation:** [CRML Specification](https://github.com/Faux16/crml/blob/main/spec/crml-1.1.md)
- **Issues:** [GitHub Issues](https://github.com/Faux16/crml/issues)
- **Discussions:** [GitHub Discussions](https://github.com/Faux16/crml/discussions)
