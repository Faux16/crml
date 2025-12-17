# Quick Start Guide (5 Minutes)

Get up and running with CRML in just 5 minutes!

## Prerequisites

- Python 3.9 or higher
- pip package manager

## Step 1: Install CRML (30 seconds)

Install the engine package to get the `crml` CLI:

```bash
pip install crml-engine
```

Verify installation:
```bash
crml --help
```

---

## Step 2: Create Your First Model (2 minutes)

Create a file called `my-first-scenario.yaml`:

```yaml
crml_scenario: "1.0"
meta:
  name: "my-first-risk-model"
  description: "A simple phishing risk model"

scenario:
  frequency:
    basis: per_organization_per_year
    model: poisson
    parameters:
      lambda: 0.10  # 10% chance per organization per year
      
  severity:
    model: lognormal
    parameters:
      median: "22 000"  # $22K median loss
      currency: USD
      sigma: 1.0        # Moderate variability
```

**What this models:**
- A single organization with a 10% annual chance of an incident
- Each incident costs ~$22K on average

If you want **multi-asset / per-asset** modeling (e.g. 100 employees, 500 endpoints), put assets in a **portfolio** document and reference one or more scenarios.

---

## Step 3: Validate Your Model (30 seconds)

```bash
crml validate my-first-scenario.yaml
```

You should see:
```
✓ CRML model is valid
```

---

## Step 4: Run Simulation (1 minute)

```bash
crml simulate my-first-scenario.yaml --runs 10000
```

You'll see results like:
```
📊 Simulation Results
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Expected Annual Loss (EAL): $220,000
VaR 95%: $450,000
VaR 99%: $650,000

Simulation completed in 1.2s
```

---

## Step 5: Try CRML Studio (1 minute)

Want a visual interface? Try CRML Studio:

```bash
# Clone the repo (if you haven't)
git clone https://github.com/Faux16/crml.git
cd crml/web

# Install and run
npm install
npm run dev
```

Visit http://localhost:3000/simulation

---

## What You Just Did

✅ Installed CRML  
✅ Created a risk model  
✅ Validated it  
✅ Ran a Monte Carlo simulation  
✅ Got risk metrics (EAL, VaR)

---

## Next Steps

### Learn More
- **[Writing CRML Models](Guides/Writing-CRML)** - Comprehensive guide
- **[Understanding Parameters](Guides/Understanding-Parameters)** - How to choose values
- **[Examples](Examples/Full-Examples)** - Pre-built models

### Try Different Scenarios
- Modify `lambda` to see how baseline threat frequency (threat likelihood) affects risk
- Change `median` to model different threat impacts (loss per event)
- Increase `cardinality` for larger organizations

### Advanced Features
- Export results: `crml simulate model.yaml --format json > results.json`
- Use in Python (language API): `from crml_lang import CRScenario`
- Use in Python (engine runtime): `from crml_engine.runtime import run_simulation`
- Build complex models with mixture distributions

---

## Common Issues

**"Command not found: crml"**
- Make sure Python's bin directory is in your PATH
- Try: `python -m crml_engine.cli --help`

**"Invalid YAML"**
- Check indentation (use spaces, not tabs)
- Run `crml validate` to see specific errors

**"Simulation takes too long"**
- Reduce `--runs` to 1000 for faster results
- Default 10,000 runs is recommended for accuracy

---

## Get Help

- 📖 [Full Documentation](Home)
- 🧪 [Interactive Simulation](http://localhost:3000/simulation)
- 💬 [GitHub Issues](https://github.com/Faux16/crml/issues)
- 📧 [Email Support](mailto:research@zeron.one)

**Ready to build real risk models?** Check out the [Writing CRML guide](Guides/Writing-CRML)!
