# Troubleshooting Guide

Common issues and how to fix them.

## Installation Issues

### "Command not found: crml"

**Problem:** After installing, `crml` command doesn't work.

**Solutions:**

1. **Check if Python's bin directory is in PATH:**
   ```bash
   # Find where crml was installed
   pip show crml-lang
   
   # Add to PATH (macOS/Linux)
   export PATH="$PATH:$HOME/.local/bin"
   
   # Add to PATH (Windows)
   set PATH=%PATH%;%APPDATA%\Python\Scripts
   ```

2. **Use Python module directly:**
   ```bash
   python -m crml.cli --help
   ```

3. **Reinstall with user flag:**
   ```bash
   pip install --user crml-lang
   ```

---

### "No module named 'crml'"

**Problem:** Python can't find the CRML module.

**Solutions:**

1. **Check installation:**
   ```bash
   pip list | grep crml
   ```

2. **Install in correct environment:**
   ```bash
   # If using virtual environment
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install crml-lang
   ```

3. **Check Python version:**
   ```bash
   python --version  # Must be 3.8+
   ```

---

## Validation Errors

### "Invalid YAML syntax"

**Problem:** YAML file won't parse.

**Common causes:**

1. **Tabs instead of spaces:**
   ```yaml
   # ❌ Wrong (tabs)
   model:
   	frequency:
   
   # ✅ Correct (spaces)
   model:
     frequency:
   ```

2. **Inconsistent indentation:**
   ```yaml
   # ❌ Wrong
   model:
     frequency:
       model: poisson
      parameters:  # Should be 4 spaces
   
   # ✅ Correct
   model:
     frequency:
       model: poisson
       parameters:
   ```

3. **Missing quotes:**
   ```yaml
   # ❌ Wrong
   meta:
     name: my-model  # Hyphen needs quotes
   
   # ✅ Correct
   meta:
     name: "my-model"
   ```

**Fix:** Use the validator to see exact error:
```bash
crml validate model.yaml
```

---

### "Missing required field"

**Problem:** Model is missing required parameters.

**Required fields:**
```yaml
crml: "1.1"  # Version (required)

model:  # Model section (required)
  frequency:  # Frequency model (required)
    model: poisson  # Model type (required)
    parameters:  # Parameters (required)
      lambda: 0.05  # Lambda value (required for Poisson)
  
  severity:  # Severity model (required)
    model: lognormal  # Model type (required)
    parameters:  # Parameters (required)
      mu: 11.5  # Mu value (required for Lognormal)
      sigma: 1.2  # Sigma value (required for Lognormal)
```

---

### "Invalid parameter value"

**Problem:** Parameter is out of valid range.

**Common issues:**

1. **Negative lambda:**
   ```yaml
   # ❌ Wrong
   lambda: -0.05
   
   # ✅ Correct
   lambda: 0.05  # Must be positive
   ```

2. **Sigma too small:**
   ```yaml
   # ❌ Wrong
   sigma: 0  # Must be > 0
   
   # ✅ Correct
   sigma: 0.5  # Positive value
   ```

3. **Lambda > 1 for Poisson:**
   ```yaml
   # ⚠️ Warning: lambda > 1 means >100% probability
   lambda: 1.5  # Probably wrong
   
   # ✅ Correct
   lambda: 0.15  # 15% probability
   ```

---

## Simulation Issues

### Results seem unrealistic

**Problem:** EAL or VaR values don't match expectations.

**Debug steps:**

1. **Check lambda interpretation:**
   ```yaml
   # Lambda is probability PER ASSET PER YEAR
   assets:
     cardinality: 100
   frequency:
     lambda: 0.10  # 10% per asset = ~10 events/year total
   ```

2. **Verify mu calculation:**
   ```python
   # Mu is ln(median_loss)
   import math
   median_loss = 100000  # $100K
   mu = math.log(median_loss)  # 11.51
   ```

3. **Check units:**
   - All losses in dollars
   - All frequencies per year
   - Cardinality = number of assets

4. **Test with known example:**
   ```bash
   # Use a validated example
   crml simulate spec/examples/data-breach-simple.yaml
   ```

---

### "Simulation takes too long"

**Problem:** Simulation runs for minutes.

**Solutions:**

1. **Reduce runs temporarily:**
   ```bash
   crml simulate model.yaml --runs 1000  # Instead of 10000
   ```

2. **Check cardinality:**
   ```yaml
   # ❌ Too high
   assets:
     cardinality: 1000000  # 1 million assets
   
   # ✅ Reasonable
   assets:
     cardinality: 1000  # 1 thousand assets
   ```

3. **Use JSON output (faster):**
   ```bash
   crml simulate model.yaml --format json > results.json
   ```

4. **Profile the model:**
   ```bash
   time crml simulate model.yaml --runs 1000
   ```

---

### "Memory error"

**Problem:** Simulation crashes with out-of-memory error.

**Solutions:**

1. **Reduce runs:**
   ```bash
   crml simulate model.yaml --runs 5000
   ```

2. **Reduce cardinality:**
   ```yaml
   assets:
     cardinality: 100  # Instead of 100000
   ```

3. **Use streaming mode** (if available):
   ```bash
   crml simulate model.yaml --stream
   ```

---

## Web Platform Issues

### "Cannot connect to localhost:3000"

**Problem:** Web platform won't load.

**Solutions:**

1. **Check if server is running:**
   ```bash
   cd web
   npm run dev
   ```

2. **Check port availability:**
   ```bash
   # Kill process on port 3000
   lsof -ti:3000 | xargs kill  # macOS/Linux
   ```

3. **Use different port:**
   ```bash
   PORT=3001 npm run dev
   ```

---

### "API simulation fails"

**Problem:** Playground simulation returns error.

**Solutions:**

1. **Check Python is available:**
   ```bash
   which python3
   python3 --version
   ```

2. **Install CRML package:**
   ```bash
   pip install crml-lang
   ```

3. **Check API logs:**
   ```bash
   # In web terminal, look for errors
   POST /api/simulate 500
   ```

4. **Test Python directly:**
   ```bash
   python3 -m crml.cli simulate spec/examples/data-breach-simple.yaml
   ```

---

## Parameter Selection Issues

### "Don't know what lambda to use"

**Problem:** Unsure about frequency parameter.

**Solutions:**

1. **Use industry data:**
   - Verizon DBIR: ~5% for data breaches
   - Sophos: ~8% for ransomware
   - KnowBe4: ~10-15% for phishing

2. **Start conservative:**
   ```yaml
   frequency:
     lambda: 0.05  # 5% - conservative estimate
   ```

3. **Use expert judgment:**
   - Ask your security team
   - Review past incidents
   - Start low, adjust up

4. **See parameter guide:**
   - [Understanding Parameters](understanding-parameters.md)
   - [Writing CRML](writing-crml.md)

---

### "Don't know what mu to use"

**Problem:** Unsure about severity parameter.

**Solutions:**

1. **Calculate from median loss:**
   ```python
   import math
   median_loss = 100000  # $100K
   mu = math.log(median_loss)  # 11.51
   ```

2. **Use industry benchmarks:**
   - IBM: $100K median for data breach → mu = 11.5
   - Coveware: $700K for ransomware → mu = 13.5

3. **Use cheat sheet:**
   | Median Loss | Mu Value |
   |-------------|----------|
   | $10K | 9.2 |
   | $50K | 10.8 |
   | $100K | 11.5 |
   | $500K | 13.1 |
   | $1M | 13.8 |

---

## Output Interpretation Issues

### "What does VaR mean?"

**Problem:** Don't understand output metrics.

**Explanations:**

**EAL (Expected Annual Loss):**
- Average loss per year
- Use for budgeting
- Example: EAL = $200K → budget $200K/year

**VaR 95% (Value at Risk):**
- 95% of years will be below this
- Only 1 in 20 years exceeds
- Use for normal worst-case planning

**VaR 99%:**
- 99% of years below this
- 1 in 100 years exceeds
- Use for stress testing

**VaR 99.9%:**
- Extreme worst-case
- 1 in 1000 years
- Use for catastrophic planning

---

### "Results vary each time"

**Problem:** Running simulation multiple times gives different results.

**This is normal!** Monte Carlo simulation is random.

**Solutions:**

1. **Use more runs for stability:**
   ```bash
   crml simulate model.yaml --runs 100000
   ```

2. **Use random seed for reproducibility:**
   ```bash
   crml simulate model.yaml --seed 42
   ```

3. **Focus on ranges, not exact values:**
   - EAL should be within ~5% each run
   - If variance is high, increase runs

---

## Integration Issues

### "Can't export to JSON"

**Problem:** JSON export fails or is malformed.

**Solutions:**

1. **Use correct flag:**
   ```bash
   crml simulate model.yaml --format json
   ```

2. **Redirect to file:**
   ```bash
   crml simulate model.yaml --format json > results.json
   ```

3. **Validate JSON:**
   ```bash
   cat results.json | python -m json.tool
   ```

---

### "Python API doesn't work"

**Problem:** Can't use CRML from Python.

**Solutions:**

1. **Check import:**
   ```python
   try:
       from crml import CRMLModel
       print("Import successful!")
   except ImportError as e:
       print(f"Error: {e}")
   ```

2. **Check installation:**
   ```bash
   pip show crml-lang
   ```

3. **Use correct syntax:**
   ```python
   from crml.runtime import run_simulation
   
   result = run_simulation("model.yaml", n_runs=10000)
   print(result["metrics"]["eal"])
   ```

---

## Still Having Issues?

### Before asking for help:

1. ✅ Check this troubleshooting guide
2. ✅ Read the [FAQ](faq.md)
3. ✅ Try the examples in `spec/examples/`
4. ✅ Validate your YAML: `crml validate model.yaml`
5. ✅ Check GitHub issues for similar problems

### Get help:

- 💬 [GitHub Discussions](https://github.com/Faux16/crml/discussions)
- 🐛 [Report a bug](https://github.com/Faux16/crml/issues/new)
- 📧 [Email support](mailto:research@zeron.one)

### When reporting issues, include:

1. CRML version: `crml --version`
2. Python version: `python --version`
3. Operating system
4. Full error message
5. Minimal example that reproduces the issue

**Example bug report:**
```
CRML Version: 1.1.0
Python: 3.9.7
OS: macOS 12.0

Error: "Invalid YAML syntax"

Steps to reproduce:
1. Create model.yaml with...
2. Run: crml validate model.yaml
3. See error: ...

Expected: Should validate successfully
Actual: Gets syntax error
```

This helps us fix issues faster!
