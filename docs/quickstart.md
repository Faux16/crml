# Quick Start Guide (5 Minutes)

Get up and running with CRML in just 5 minutes!

## Prerequisites

- Python 3.8 or higher
- pip package manager

## Step 1: Install CRML (30 seconds)

```bash
pip install crml-lang
```

Verify installation:
```bash
crml --version
```

---

## Step 2: Create Your First Model (2 minutes)

Create a file called `my-first-model.yaml`:

```yaml
crml: "1.1"
meta:
  name: "my-first-risk-model"
  description: "A simple phishing risk model"

model:
  assets:
    cardinality: 100  # 100 employees
    
  frequency:
    model: poisson
    parameters:
      lambda: 0.10  # 10% chance per employee per year
      
  severity:
    model: lognormal
    parameters:
      median: "22 000"  # $22K median loss
      currency: USD
      sigma: 1.0        # Moderate variability
```

**What this models:**
- 100 employees, each with 10% chance of clicking a phishing link
- Expected ~10 incidents per year
- Each incident costs ~$22K on average

---

## Step 3: Validate Your Model (30 seconds)

```bash
crml validate my-first-model.yaml
```

You should see:
```
✓ CRML model is valid
```

---

## Step 4: Run Simulation (1 minute)

```bash
crml simulate my-first-model.yaml --runs 10000
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

## Step 5: Try the Web Platform (1 minute)

Want a visual interface? Try the interactive playground:

```bash
# Clone the repo (if you haven't)
git clone https://github.com/Faux16/crml.git
cd crml/web

# Install and run
npm install
npm run dev
```

Visit http://localhost:3000/playground

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
- **[Writing CRML Models](writing-crml.md)** - Comprehensive guide
- **[Understanding Parameters](understanding-parameters.md)** - How to choose values
- **[Examples](examples/full_examples.md)** - Pre-built models

### Try Different Scenarios
- Modify `lambda` to see how frequency affects risk
- Change `median` to model different loss amounts
- Increase `cardinality` for larger organizations

### Advanced Features
- Export results: `crml simulate model.yaml --format json > results.json`
- Use in Python: `from crml import CRMLModel`
- Build complex models with mixture distributions

---

## Common Issues

**"Command not found: crml"**
- Make sure Python's bin directory is in your PATH
- Try: `python -m crml.cli --help`

**"Invalid YAML"**
- Check indentation (use spaces, not tabs)
- Run `crml validate` to see specific errors

**"Simulation takes too long"**
- Reduce `--runs` to 1000 for faster results
- Default 10,000 runs is recommended for accuracy

---

## Get Help

- 📖 [Full Documentation](index.md)
- 🎮 [Interactive Playground](http://localhost:3000/playground)
- 💬 [GitHub Issues](https://github.com/Faux16/crml/issues)
- 📧 [Email Support](mailto:research@zeron.one)

**Ready to build real risk models?** Check out the [Writing CRML guide](writing-crml.md)!
