# How to Calibrate Models from Historical Data

Learn how to use your organization's actual incident data to improve CRML model accuracy.

## Why Calibrate?

**Before calibration:** Use industry averages (e.g., 5% breach rate)  
**After calibration:** Use your actual data (e.g., 3.2% based on 3 years of incidents)

**Benefits:**
- More accurate risk estimates
- Tailored to your organization
- Defensible in audits
- Track improvement over time

---

## What Data Do You Need?

### Minimum Requirements

**For Frequency (Lambda):**
- Number of incidents per year
- Number of assets at risk
- Time period (minimum 1 year, ideally 3+ years)

**For Severity (Mu, Sigma):**
- Cost of each incident
- At least 10-20 incidents for statistical validity

### Example Data Collection

```csv
Date,Incident_Type,Cost_USD,Assets_Affected
2023-01-15,Phishing,25000,1
2023-03-22,Phishing,18000,1
2023-05-10,Malware,45000,1
2023-07-18,Phishing,32000,1
2023-09-05,Phishing,21000,1
2023-11-12,Phishing,28000,1
```

---

## Step 1: Calculate Frequency (Lambda)

### Formula

```
Lambda = Total Incidents / (Assets × Years)
```

### Example

```python
# Your data
total_incidents = 18  # Over 3 years
total_assets = 500    # Employees
years = 3

# Calculate lambda
lambda_value = total_incidents / (total_assets * years)
# lambda_value = 18 / (500 * 3) = 0.012

print(f"Lambda: {lambda_value:.3f}")  # 0.012 or 1.2%
```

### In CRML

```yaml
frequency:
  model: poisson
  parameters:
    lambda: 0.012  # Your calibrated value
```

---

## Step 2: Calculate Severity (Mu, Sigma)

### Formula

```
Mu = ln(median_loss)
Sigma = sqrt(variance of ln(losses))
```

### Example

```python
import numpy as np
import math

# Your incident costs
losses = [25000, 18000, 45000, 32000, 21000, 28000, 
          35000, 22000, 41000, 19000, 27000, 38000]

# Calculate median
median_loss = np.median(losses)
mu = math.log(median_loss)

# Calculate sigma
log_losses = [math.log(loss) for loss in losses]
sigma = np.std(log_losses)

print(f"Median loss: ${median_loss:,.0f}")
print(f"Mu: {mu:.2f}")
print(f"Sigma: {sigma:.2f}")
```

**Output:**
```
Median loss: $27,500
Mu: 10.22
Sigma: 0.35
```

### In CRML

```yaml
severity:
  model: lognormal
  parameters:
    mu: 10.22    # Your calibrated value
    sigma: 0.35  # Your calibrated value
```

---

## Step 3: Validate Your Calibration

### Compare to Industry Data

```python
# Your calibrated lambda
your_lambda = 0.012  # 1.2%

# Industry benchmark (e.g., Verizon DBIR)
industry_lambda = 0.05  # 5%

if your_lambda < industry_lambda:
    print("✓ Your controls are working better than average!")
else:
    print("⚠ Consider strengthening controls")
```

### Run Simulation

```bash
# Create calibrated model
crml simulate calibrated-model.yaml --runs 10000

# Compare to baseline
crml simulate industry-baseline.yaml --runs 10000
```

**Expected:** Your EAL should be lower if you have better controls.

---

## Complete Calibration Script

Save as `calibrate.py`:

```python
#!/usr/bin/env python3
"""
CRML Model Calibration Tool
Calibrates frequency and severity from historical incident data
"""

import numpy as np
import math
import yaml
import sys

def calibrate_frequency(incidents, assets, years):
    """Calculate lambda from incident history"""
    lambda_val = incidents / (assets * years)
    return lambda_val

def calibrate_severity(losses):
    """Calculate mu and sigma from loss amounts"""
    if len(losses) < 10:
        print("⚠ Warning: Less than 10 incidents. Results may be unreliable.")
    
    median_loss = np.median(losses)
    mu = math.log(median_loss)
    
    log_losses = [math.log(loss) for loss in losses]
    sigma = np.std(log_losses)
    
    return mu, sigma, median_loss

def main():
    print("CRML Model Calibration Tool")
    print("=" * 50)
    
    # Frequency calibration
    print("\n1. FREQUENCY CALIBRATION")
    print("-" * 50)
    incidents = int(input("Total incidents (last 3 years): "))
    assets = int(input("Number of assets at risk: "))
    years = int(input("Time period (years): "))
    
    lambda_val = calibrate_frequency(incidents, assets, years)
    print(f"\n✓ Calibrated Lambda: {lambda_val:.4f} ({lambda_val*100:.2f}%)")
    
    # Severity calibration
    print("\n2. SEVERITY CALIBRATION")
    print("-" * 50)
    print("Enter incident costs (one per line, empty line to finish):")
    
    losses = []
    while True:
        try:
            loss = input(f"Incident {len(losses)+1} cost ($): ")
            if not loss:
                break
            losses.append(float(loss))
        except ValueError:
            print("Invalid input. Please enter a number.")
    
    if len(losses) == 0:
        print("No losses entered. Skipping severity calibration.")
        return
    
    mu, sigma, median = calibrate_severity(losses)
    print(f"\n✓ Calibrated Mu: {mu:.2f}")
    print(f"✓ Calibrated Sigma: {sigma:.2f}")
    print(f"  (Median loss: ${median:,.0f})")
    
    # Generate CRML model
    print("\n3. GENERATED CRML MODEL")
    print("-" * 50)
    
    model = {
        'crml': '1.1',
        'meta': {
            'name': 'calibrated-model',
            'description': 'Model calibrated from historical data',
            'calibration_date': '2024-01-01',
            'data_period': f'{years} years',
            'incident_count': incidents
        },
        'model': {
            'assets': {
                'cardinality': assets
            },
            'frequency': {
                'model': 'poisson',
                'parameters': {
                    'lambda': round(lambda_val, 4)
                }
            },
            'severity': {
                'model': 'lognormal',
                'parameters': {
                    'mu': round(mu, 2),
                    'sigma': round(sigma, 2)
                }
            }
        }
    }
    
    print(yaml.dump(model, default_flow_style=False))
    
    # Save to file
    filename = input("\nSave to file (default: calibrated-model.yaml): ") or "calibrated-model.yaml"
    with open(filename, 'w') as f:
        yaml.dump(model, f, default_flow_style=False)
    
    print(f"\n✓ Model saved to {filename}")
    print(f"\nRun simulation: crml simulate {filename}")

if __name__ == '__main__':
    main()
```

### Usage

```bash
python calibrate.py
```

**Interactive prompts:**
```
Total incidents (last 3 years): 18
Number of assets at risk: 500
Time period (years): 3

✓ Calibrated Lambda: 0.0120 (1.20%)

Enter incident costs (one per line, empty line to finish):
Incident 1 cost ($): 25000
Incident 2 cost ($): 18000
...

✓ Calibrated Mu: 10.22
✓ Calibrated Sigma: 0.35
  (Median loss: $27,500)

✓ Model saved to calibrated-model.yaml
```

---

## Best Practices

### 1. Use Enough Data

**Minimum:**
- 1 year of data
- 10+ incidents

**Ideal:**
- 3+ years of data
- 30+ incidents

**If you have less:** Use industry data and note it as an assumption.

### 2. Clean Your Data

```python
# Remove outliers (optional)
def remove_outliers(losses, std_devs=3):
    mean = np.mean(losses)
    std = np.std(losses)
    return [x for x in losses if abs(x - mean) < std_devs * std]

# Example
raw_losses = [25000, 18000, 5000000, 32000]  # 5M is outlier
clean_losses = remove_outliers(raw_losses)
```

### 3. Document Everything

```yaml
meta:
  name: "calibrated-phishing-2024"
  calibration_date: "2024-01-15"
  data_source: "SIEM logs 2021-2023"
  incident_count: 18
  notes: "Excluded 1 outlier ($5M wire fraud)"
```

### 4. Update Regularly

```bash
# Quarterly calibration
Q1: calibrate.py → model-2024-q1.yaml
Q2: calibrate.py → model-2024-q2.yaml
Q3: calibrate.py → model-2024-q3.yaml
Q4: calibrate.py → model-2024-q4.yaml

# Compare trends
python compare-models.py model-2024-*.yaml
```

---

## Advanced: Bayesian Calibration

For more sophisticated calibration using prior beliefs + data:

```python
import pymc as pm

# Define prior (industry data)
prior_lambda = 0.05  # 5% industry average

# Your observed data
observed_incidents = 18
observed_assets = 500
observed_years = 3

# Bayesian model
with pm.Model() as model:
    # Prior: industry average
    lambda_prior = pm.Beta('lambda', alpha=5, beta=95)  # ~5%
    
    # Likelihood: your data
    incidents = pm.Poisson('incidents', 
                          mu=lambda_prior * observed_assets * observed_years,
                          observed=observed_incidents)
    
    # Posterior: updated belief
    trace = pm.sample(2000)

# Get calibrated lambda
lambda_calibrated = trace.posterior['lambda'].mean()
print(f"Calibrated lambda: {lambda_calibrated:.4f}")
```

---

## Troubleshooting

### "Not enough data"

**Solution:** Combine with industry data
```python
# Weight your data with industry data
your_lambda = 0.012  # From 18 incidents
industry_lambda = 0.05  # Industry average

# Weighted average (50/50)
calibrated_lambda = (your_lambda + industry_lambda) / 2
# = 0.031 or 3.1%
```

### "Results don't make sense"

**Check:**
1. Are you counting all incidents?
2. Is asset count correct?
3. Are costs complete (include hidden costs)?
4. Any data entry errors?

### "Too much variability"

**Solution:** Use mixture model
```yaml
severity:
  model: mixture
  components:
    - lognormal:  # Small incidents (80%)
        weight: 0.8
        mu: 10.0
        sigma: 0.5
    - lognormal:  # Large incidents (20%)
        weight: 0.2
        mu: 12.5
        sigma: 1.0
```

---

## Next Steps

1. **Collect your data** - Start tracking incidents systematically
2. **Run calibration** - Use the script above
3. **Compare to baseline** - See if your controls are working
4. **Update quarterly** - Track trends over time
5. **Present results** - Show executives your improving risk posture

---

## See Also

- [Writing CRML](../writing-crml.md) - Model creation basics
- [FAQ](../faq.md) - Common calibration questions
- [Executive Reporting](executive-reporting.md) - Present calibrated results
