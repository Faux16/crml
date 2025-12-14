# How to Integrate CRML with Other Tools

Connect CRML to your existing security and GRC tools.

## Overview

CRML can integrate with:
- **SIEM** (Splunk, Elastic, QRadar) - Auto-update parameters from real data
- **GRC Platforms** (ServiceNow, Archer, LogicGate) - Import/export risk assessments
- **Ticketing** (Jira, ServiceNow) - Track incidents for calibration
- **BI Tools** (Tableau, Power BI) - Visualize risk trends
- **CI/CD** (GitHub Actions, GitLab CI) - Automate risk reporting

---

## JSON API Integration

### Export CRML Results

```bash
# Get JSON output
crml simulate model.yaml --format json > results.json
```

**Output structure:**
```json
{
  "success": true,
  "metrics": {
    "eal": 220000,
    "var_95": 450000,
    "var_99": 650000,
    "var_999": 900000
  },
  "distribution": {
    "bins": [0, 50000, 100000, ...],
    "frequencies": [1200, 800, 600, ...]
  },
  "metadata": {
    "runs": 10000,
    "runtime_ms": 1234
  }
}
```

### Parse in Python

```python
import json
import requests

# Run simulation
result = json.loads(open('results.json').read())

# Extract metrics
eal = result['metrics']['eal']
var_95 = result['metrics']['var_95']

# Send to GRC platform
requests.post('https://grc.example.com/api/risks', json={
    'risk_id': 'CYBER-001',
    'eal': eal,
    'var_95': var_95,
    'updated_at': '2024-01-15'
})
```

---

## SIEM Integration

### Splunk

**Auto-calibrate from SIEM data:**

```python
#!/usr/bin/env python3
"""
Splunk to CRML Calibration
Queries Splunk for incidents, calibrates CRML model
"""

import splunklib.client as client
import splunklib.results as results
import yaml
import math
import numpy as np

# Connect to Splunk
service = client.connect(
    host='splunk.example.com',
    port=8089,
    username='admin',
    password='password'
)

# Query incidents (last 365 days)
query = '''
search index=security sourcetype=incident
| where severity="high" OR severity="critical"
| stats count as incidents, values(cost) as costs
'''

job = service.jobs.create(query)
# Wait for job to complete...

# Get results
for result in results.ResultsReader(job.results()):
    incidents = int(result['incidents'])
    costs = [float(c) for c in result['costs']]

# Calibrate
lambda_val = incidents / (500 * 1)  # 500 assets, 1 year
mu = math.log(np.median(costs))
sigma = np.std([math.log(c) for c in costs])

# Generate CRML model
model = {
    'crml': '1.1',
    'meta': {
        'name': 'splunk-calibrated',
        'source': 'Splunk SIEM',
        'last_updated': '2024-01-15'
    },
    'model': {
        'assets': {'cardinality': 500},
        'frequency': {
            'model': 'poisson',
            'parameters': {'lambda': lambda_val}
        },
        'severity': {
            'model': 'lognormal',
            'parameters': {'mu': mu, 'sigma': sigma}
        }
    }
}

# Save
with open('splunk-calibrated.yaml', 'w') as f:
    yaml.dump(model, f)

print("✓ Model calibrated from Splunk data")
```

### Elastic Security

```python
from elasticsearch import Elasticsearch

# Connect
es = Elasticsearch(['https://elastic.example.com:9200'])

# Query incidents
query = {
    "query": {
        "range": {
            "@timestamp": {
                "gte": "now-1y"
            }
        }
    },
    "aggs": {
        "incident_count": {"value_count": {"field": "event.id"}},
        "costs": {"terms": {"field": "incident.cost"}}
    }
}

result = es.search(index="security-*", body=query)

# Extract and calibrate...
```

---

## GRC Platform Integration

### ServiceNow

**Push CRML results to ServiceNow Risk table:**

```python
import requests
import json

# ServiceNow credentials
SNOW_INSTANCE = 'https://yourinstance.service-now.com'
SNOW_USER = 'admin'
SNOW_PASS = 'password'

# CRML results
crml_results = json.loads(open('results.json').read())

# Create/update risk in ServiceNow
risk_data = {
    'short_description': 'Phishing Risk Assessment',
    'risk_statement': f"Expected annual loss: ${crml_results['metrics']['eal']:,.0f}",
    'impact': 'High' if crml_results['metrics']['eal'] > 500000 else 'Medium',
    'u_eal': crml_results['metrics']['eal'],
    'u_var_95': crml_results['metrics']['var_95'],
    'u_var_99': crml_results['metrics']['var_99']
}

response = requests.post(
    f'{SNOW_INSTANCE}/api/now/table/sn_risk_risk',
    auth=(SNOW_USER, SNOW_PASS),
    headers={'Content-Type': 'application/json'},
    json=risk_data
)

if response.status_code == 201:
    print("✓ Risk created in ServiceNow")
else:
    print(f"✗ Error: {response.text}")
```

### Archer

```python
# Similar pattern for Archer GRC
import requests

ARCHER_URL = 'https://archer.example.com/api'
ARCHER_TOKEN = 'your-token'

# Map CRML to Archer fields
archer_data = {
    'ContentId': 12345,  # Risk record ID
    'FieldContents': {
        'Risk Name': 'Phishing Attacks',
        'Expected Annual Loss': crml_results['metrics']['eal'],
        'VaR 95%': crml_results['metrics']['var_95'],
        'Assessment Date': '2024-01-15'
    }
}

# Update record
requests.put(
    f'{ARCHER_URL}/core/content',
    headers={'Authorization': f'Archer session-id={ARCHER_TOKEN}'},
    json=archer_data
)
```

---

## Jira Integration

**Track incidents for calibration:**

```python
from jira import JIRA

# Connect
jira = JIRA('https://jira.example.com', basic_auth=('user', 'pass'))

# Query security incidents
issues = jira.search_issues('project=SEC AND type=Incident AND created >= -365d')

# Extract costs
incidents = []
for issue in issues:
    cost = issue.fields.customfield_10050  # Cost field
    if cost:
        incidents.append({
            'date': issue.fields.created,
            'cost': float(cost),
            'type': issue.fields.summary
        })

# Calibrate CRML model
lambda_val = len(incidents) / (500 * 1)  # 500 assets, 1 year
costs = [i['cost'] for i in incidents]
# ... (calibration logic)

print(f"✓ Calibrated from {len(incidents)} Jira incidents")
```

---

## CI/CD Automation

### GitHub Actions

`.github/workflows/risk-assessment.yml`:

```yaml
name: Monthly Risk Assessment

on:
  schedule:
    - cron: '0 0 1 * *'  # First day of month
  workflow_dispatch:  # Manual trigger

jobs:
  assess-risk:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install CRML
        run: pip install crml-lang
      
      - name: Run Simulation
        run: |
          crml simulate models/phishing-risk.yaml --format json > results.json
      
      - name: Upload to GRC
        env:
          GRC_API_KEY: ${{ secrets.GRC_API_KEY }}
        run: |
          python scripts/upload-to-grc.py results.json
      
      - name: Create Issue if High Risk
        run: |
          EAL=$(jq '.metrics.eal' results.json)
          if (( $(echo "$EAL > 1000000" | bc -l) )); then
            gh issue create \
              --title "High Risk Alert: EAL exceeds $1M" \
              --body "Current EAL: \$$EAL. Review required."
          fi
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### GitLab CI

`.gitlab-ci.yml`:

```yaml
risk-assessment:
  stage: security
  image: python:3.9
  script:
    - pip install crml-lang
    - crml simulate models/risk.yaml --format json > results.json
    - python scripts/upload-results.py
  artifacts:
    paths:
      - results.json
    expire_in: 1 year
  only:
    - schedules
```

---

## Power BI / Tableau

### Export Time Series Data

```python
import pandas as pd
import json
from datetime import datetime, timedelta

# Run simulations for each month
results = []
for month in range(12):
    date = datetime.now() - timedelta(days=30*month)
    
    # Run simulation
    result = json.loads(open(f'results-{month}.json').read())
    
    results.append({
        'date': date.strftime('%Y-%m-%d'),
        'eal': result['metrics']['eal'],
        'var_95': result['metrics']['var_95'],
        'var_99': result['metrics']['var_99']
    })

# Create DataFrame
df = pd.DataFrame(results)

# Export for Power BI
df.to_csv('risk-trends.csv', index=False)

# Or export to SQL
from sqlalchemy import create_engine
engine = create_engine('postgresql://user:pass@localhost/riskdb')
df.to_sql('risk_metrics', engine, if_exists='append')
```

### Power BI Connection

```python
# In Power BI, use Python script data source:
import pandas as pd
import subprocess
import json

# Run CRML simulation
result = subprocess.run(
    ['crml', 'simulate', 'model.yaml', '--format', 'json'],
    capture_output=True,
    text=True
)

data = json.loads(result.stdout)

# Create DataFrame for Power BI
df = pd.DataFrame([{
    'Metric': 'EAL',
    'Value': data['metrics']['eal']
}, {
    'Metric': 'VaR 95%',
    'Value': data['metrics']['var_95']
}, {
    'Metric': 'VaR 99%',
    'Value': data['metrics']['var_99']
}])
```

---

## Webhook Integration

**Trigger simulation on events:**

```python
from flask import Flask, request
import subprocess
import json

app = Flask(__name__)

@app.route('/webhook/incident', methods=['POST'])
def handle_incident():
    """Triggered when new incident is created"""
    
    incident = request.json
    
    # Update model with new data
    # ... (calibration logic)
    
    # Run simulation
    result = subprocess.run(
        ['crml', 'simulate', 'updated-model.yaml', '--format', 'json'],
        capture_output=True,
        text=True
    )
    
    data = json.loads(result.stdout)
    
    # Alert if risk increased significantly
    if data['metrics']['eal'] > 500000:
        send_alert(f"Risk increased to ${data['metrics']['eal']:,.0f}")
    
    return {'status': 'processed'}

if __name__ == '__main__':
    app.run(port=5000)
```

---

## Best Practices

### 1. Automate Updates

```bash
# Cron job: Daily calibration from SIEM
0 2 * * * /usr/local/bin/calibrate-from-siem.py

# Cron job: Weekly risk report
0 9 * * 1 /usr/local/bin/generate-risk-report.sh
```

### 2. Version Control Models

```bash
# Git track your models
git add models/phishing-risk.yaml
git commit -m "Updated lambda based on Q4 data"
git tag v2024-q4
```

### 3. API Rate Limiting

```python
import time
from functools import wraps

def rate_limit(calls_per_minute=10):
    min_interval = 60.0 / calls_per_minute
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            last_called[0] = time.time()
            return func(*args, **kwargs)
        return wrapper
    return decorator

@rate_limit(calls_per_minute=10)
def upload_to_grc(data):
    # API call here
    pass
```

### 4. Error Handling

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    result = run_simulation('model.yaml')
    upload_to_grc(result)
    logger.info("✓ Risk assessment completed")
except Exception as e:
    logger.error(f"✗ Error: {e}")
    send_alert(f"Risk assessment failed: {e}")
```

---

## Example: Complete Integration

**Full workflow:**

```python
#!/usr/bin/env python3
"""
Complete CRML Integration Workflow
1. Fetch incidents from SIEM
2. Calibrate model
3. Run simulation
4. Upload to GRC
5. Generate report
6. Send notifications
"""

import logging
from datetime import datetime
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting risk assessment workflow")
    
    # 1. Fetch from SIEM
    logger.info("Fetching incidents from Splunk...")
    incidents = fetch_from_splunk()
    logger.info(f"Found {len(incidents)} incidents")
    
    # 2. Calibrate
    logger.info("Calibrating model...")
    model = calibrate_model(incidents)
    save_model(model, 'calibrated-model.yaml')
    
    # 3. Simulate
    logger.info("Running simulation...")
    results = run_simulation('calibrated-model.yaml')
    
    # 4. Upload to GRC
    logger.info("Uploading to ServiceNow...")
    upload_to_servicenow(results)
    
    # 5. Generate report
    logger.info("Generating report...")
    report = generate_report(results)
    save_report(report, f'report-{datetime.now().strftime("%Y%m%d")}.pdf')
    
    # 6. Notify
    if results['metrics']['eal'] > 1000000:
        logger.warning("High risk detected!")
        send_alert(results)
    
    logger.info("✓ Workflow completed successfully")

if __name__ == '__main__':
    main()
```

---

## See Also

- [Calibration Guide](calibrate-from-data.md) - Prepare data for integration
- [Executive Reporting](executive-reporting.md) - Present integrated results
- [FAQ](../faq.md) - Common integration questions
