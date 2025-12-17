# Getting Started with CRML

This guide will help you install CRML and run your first cyber risk simulation.

---

## Installation

For platform-specific install steps, see:

- [Installation](Installation)
- [Quickstart](Quickstart)

If you want the CLI, install:

```bash
pip install crml-engine
```

---

## Your First Scenario

Let's create a simple ransomware risk model.

### 1. Create a YAML file

Create a file named `ransomware.yaml`:

```yaml
crml_scenario: "1.0"

meta:
  name: "simple-ransomware"
  description: "Basic ransomware risk model"
  author: "Your Name"

scenario:
  frequency:
    basis: per_organization_per_year
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
[OK] ransomware.yaml is a valid CRML scenario document.
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

In current CRML, controls are typically applied via a **portfolio**:

- The **scenario** references controls by id (and can add scenario-specific applicability factors).
- The **portfolio** provides the control inventory/assessment (effectiveness, coverage, reliability, and optional dependency).

### 1) Reference a control from the scenario

Update `ransomware.yaml` to include a control id (example uses the sample control pack id `org:edr`):

```yaml
crml_scenario: "1.0"

meta:
  name: "simple-ransomware"
  description: "Basic ransomware risk model"
  author: "Your Name"

scenario:
  frequency:
    basis: per_organization_per_year
    model: poisson
    parameters:
      lambda: 0.12

  severity:
    model: lognormal
    parameters:
      median: "500 000"
      currency: USD
      sigma: 1.5

  controls:
    - id: "org:edr"
      implementation_effectiveness: 1.0
      coverage:
        value: 1.0
        basis: endpoints
```

### 2) Create a portfolio that supplies control data

Create `ransomware-portfolio.yaml` (in the repo root, so the `examples/...` paths resolve):

```yaml
crml_portfolio: "1.0"
meta:
  name: "ransomware-portfolio"

portfolio:
  semantics:
    method: sum
    constraints:
      require_paths_exist: true
      validate_scenarios: true

  control_catalogs:
    - examples/control_cataloges/control-catalog.yaml
  control_assessments:
    - examples/control_assessments/control-assessment.yaml

  scenarios:
    - id: ransomware
      path: ransomware.yaml
```

### 3) Simulate the portfolio

```bash
crml simulate ransomware-portfolio.yaml --runs 10000
```

---

## Multi-Currency Support

Model risks in different currencies:

```yaml
scenario:
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

Specify output currency via an FX config file:

```bash
crml simulate scenario.yaml --fx-config examples/fx_configs/fx-config.yaml
```

---

## Auto-Calibration from Data

Have historical loss data? Let CRML calibrate parameters automatically:

```yaml
crml_scenario: "1.0"
meta: {name: "calibrated-example"}
scenario:
  frequency:
    basis: per_organization_per_year
    model: poisson
    parameters: {lambda: 0.1}

  severity:
    model: lognormal
    parameters:
      currency: USD
      single_losses:
        - 125000
        - 450000
        - 89000
        - 1200000
        - 67000
      # If provided, the reference engine auto-calibrates lognormal mu/sigma from these samples.
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
python -m crml_engine.cli validate model.yaml
```

### "Invalid CRML document"

Check that:
1. YAML syntax is correct (use a YAML validator)
2. `crml_scenario: "1.0"` is specified at the top
3. All required fields are present
4. Parameter values are in valid ranges

---

## Getting Help

- **Documentation:** [CRML Specification](Reference/CRML-1.1)
- **Issues:** [GitHub Issues](https://github.com/Faux16/crml/issues)
- **Discussions:** [GitHub Discussions](https://github.com/Faux16/crml/discussions)
