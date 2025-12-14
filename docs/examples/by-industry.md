# Industry-Specific Examples

Real-world CRML models for different industries.

## Healthcare

### HIPAA Data Breach

**Scenario:** Protected Health Information (PHI) breach affecting patient records.

```yaml
crml: "1.1"
meta:
  name: "healthcare-phi-breach"
  description: "HIPAA-regulated PHI breach risk"
  industry: "Healthcare"
  compliance: ["HIPAA", "HITECH"]
  
model:
  assets:
    cardinality: 250  # 250 databases with PHI
    
  frequency:
    model: poisson
    parameters:
      lambda: 0.04  # 4% annual breach rate (HHS data)
      
  severity:
    model: lognormal
    parameters:
      mu: 12.2    # ~$200K median (Ponemon Healthcare Breach Study)
      sigma: 1.5  # High variability ($50K-$2M range)
```

**Data sources:**
- HHS Breach Portal: 4% of covered entities breached annually
- Ponemon Institute Healthcare Breach Study: $200K median cost
- Includes: HIPAA fines, notification costs, credit monitoring, legal fees

**Expected results:**
- EAL: ~$2M/year
- VaR 95%: ~$4.5M
- Budget for breach response team and cyber insurance

---

### Medical Device Vulnerability

**Scenario:** Exploitable vulnerabilities in connected medical devices.

```yaml
crml: "1.1"
meta:
  name: "medical-device-vuln"
  description: "IoMT device vulnerability exploitation"
  industry: "Healthcare"
  
model:
  assets:
    cardinality: 500  # 500 connected devices
    
  frequency:
    model: poisson
    parameters:
      lambda: 0.02  # 2% exploitation rate
      
  severity:
    model: lognormal
    parameters:
      mu: 13.5    # ~$700K (patient safety incident + regulatory)
      sigma: 2.0  # Extreme variability
```

---

## Financial Services

### Payment Card Data Breach

**Scenario:** PCI DSS breach affecting credit card data.

```yaml
crml: "1.1"
meta:
  name: "pci-breach"
  description: "Payment card data breach (PCI DSS)"
  industry: "Financial Services"
  compliance: ["PCI DSS"]
  
model:
  assets:
    cardinality: 100  # 100 payment processing systems
    
  frequency:
    model: poisson
    parameters:
      lambda: 0.03  # 3% annual breach rate (Verizon DBIR)
      
  severity:
    model: lognormal
    parameters:
      mu: 13.8    # ~$1M median (PCI fines + card reissuance)
      sigma: 1.8  # High variability
```

**Data sources:**
- Verizon DBIR: 3% of financial institutions breached
- PCI fines: $5K-$100K per month
- Card reissuance: $5-$10 per card
- Reputation damage: 10-30% of breach cost

---

### Wire Fraud (BEC)

**Scenario:** Business Email Compromise leading to fraudulent wire transfers.

```yaml
crml: "1.1"
meta:
  name: "wire-fraud-bec"
  description: "Business Email Compromise wire fraud"
  industry: "Financial Services"
  
model:
  assets:
    cardinality: 50  # 50 employees with wire transfer authority
    
  frequency:
    model: poisson
    parameters:
      lambda: 0.08  # 8% targeted annually (FBI IC3)
      
  severity:
    model: lognormal
    parameters:
      mu: 13.1    # ~$500K median transfer (FBI IC3 data)
      sigma: 1.5  # Moderate-high variability
```

**Data sources:**
- FBI IC3 Report: $500K median BEC loss
- 8% of finance employees targeted annually

---

## Retail

### Point-of-Sale (POS) Breach

**Scenario:** POS system compromise affecting customer payment data.

```yaml
crml: "1.1"
meta:
  name: "pos-breach"
  description: "Point-of-sale system breach"
  industry: "Retail"
  compliance: ["PCI DSS"]
  
model:
  assets:
    cardinality: 200  # 200 POS terminals
    
  frequency:
    model: poisson
    parameters:
      lambda: 0.05  # 5% breach rate (Verizon DBIR retail sector)
      
  severity:
    model: lognormal
    parameters:
      mu: 14.5    # ~$2M median (Target/Home Depot scale)
      sigma: 2.0  # Extreme variability
```

**Data sources:**
- Verizon DBIR Retail Sector: 5% annual breach rate
- Target breach: $18.5M settlement
- Home Depot: $19.5M settlement
- Median for smaller retailers: ~$2M

---

### E-Commerce Platform Breach

**Scenario:** Online store database breach exposing customer data.

```yaml
crml: "1.1"
meta:
  name: "ecommerce-breach"
  description: "E-commerce customer database breach"
  industry: "Retail"
  
model:
  assets:
    cardinality: 10  # 10 customer databases
    
  frequency:
    model: poisson
    parameters:
      lambda: 0.06  # 6% annual breach rate
      
  severity:
    model: mixture
    components:
      - lognormal:  # 70% are moderate breaches
          weight: 0.7
          mu: 11.5   # ~$100K
          sigma: 1.0
      - lognormal:  # 30% are severe (with PII)
          weight: 0.3
          mu: 14.0   # ~$1.2M
          sigma: 1.5
```

---

## SaaS / Technology

### Cloud Service Outage

**Scenario:** SaaS platform outage affecting customers.

```yaml
crml: "1.1"
meta:
  name: "saas-outage"
  description: "SaaS platform availability incident"
  industry: "Technology"
  
model:
  frequency:
    model: poisson
    scope: portfolio  # Organization-wide impact
    parameters:
      lambda: 3.0  # 3 significant outages per year
      
  severity:
    model: lognormal
    parameters:
      mu: 12.5    # ~$270K per outage (SLA credits + churn)
      sigma: 1.2  # Moderate variability
```

**Cost breakdown:**
- SLA credits: 10-25% of MRR
- Customer churn: 5-15% after major outage
- Reputation damage
- Engineering response costs

---

### API Security Breach

**Scenario:** API vulnerability leading to data exposure.

```yaml
crml: "1.1"
meta:
  name: "api-breach"
  description: "API security vulnerability exploitation"
  industry: "Technology"
  
model:
  assets:
    cardinality: 50  # 50 public APIs
    
  frequency:
    model: poisson
    parameters:
      lambda: 0.10  # 10% have exploitable vulns (Salt Security)
      
  severity:
    model: lognormal
    parameters:
      mu: 13.0    # ~$440K median
      sigma: 1.8  # High variability
```

**Data sources:**
- Salt Security API Security Report
- OWASP API Security Top 10

---

## Manufacturing

### Ransomware on OT/ICS

**Scenario:** Ransomware affecting operational technology systems.

```yaml
crml: "1.1"
meta:
  name: "ot-ransomware"
  description: "Ransomware on operational technology"
  industry: "Manufacturing"
  
model:
  assets:
    cardinality: 100  # 100 OT/ICS systems
    
  frequency:
    model: poisson
    parameters:
      lambda: 0.12  # 12% (higher than IT due to legacy systems)
      
  severity:
    model: lognormal
    parameters:
      mu: 14.8    # ~$2.7M (ransom + downtime + recovery)
      sigma: 2.0  # Extreme variability
```

**Cost factors:**
- Production downtime: $100K-$1M per day
- Ransom payment: $50K-$500K
- System recovery: weeks to months
- Supply chain impact

---

## Education

### Student Data Breach

**Scenario:** FERPA-protected student records breach.

```yaml
crml: "1.1"
meta:
  name: "student-data-breach"
  description: "FERPA student records breach"
  industry: "Education"
  compliance: ["FERPA"]
  
model:
  assets:
    cardinality: 50  # 50 student information systems
    
  frequency:
    model: poisson
    parameters:
      lambda: 0.07  # 7% annual breach rate (K12 Cybersecurity Report)
      
  severity:
    model: lognormal
    parameters:
      mu: 11.0    # ~$60K median (smaller than commercial)
      sigma: 1.5  # High variability
```

---

## Using These Examples

### Customize for Your Organization

1. **Adjust cardinality:**
   ```yaml
   assets:
     cardinality: YOUR_ASSET_COUNT
   ```

2. **Refine lambda based on your controls:**
   ```yaml
   # Industry baseline: 0.05
   # With strong controls: 0.02 (60% reduction)
   # With weak controls: 0.08 (60% increase)
   ```

3. **Adjust severity for your size:**
   ```yaml
   # Small org: mu = 10.0 (~$22K)
   # Medium org: mu = 12.0 (~$160K)
   # Large org: mu = 14.0 (~$1.2M)
   ```

### Combine Multiple Risks

```bash
# Run each scenario
crml simulate healthcare-phi-breach.yaml > phi-results.json
crml simulate medical-device-vuln.yaml > device-results.json

# Aggregate in Python
python aggregate-risks.py phi-results.json device-results.json
```

### Track Over Time

```bash
# Q1
crml simulate model.yaml --seed 1 > q1-results.json

# Q2 (after implementing controls)
# Update lambda to reflect control effectiveness
crml simulate model.yaml --seed 2 > q2-results.json

# Compare
python compare-results.py q1-results.json q2-results.json
```

---

## Data Sources

### Industry Reports
- **Verizon DBIR** - Annual breach statistics by industry
- **IBM Cost of Data Breach** - Loss amounts by industry/region
- **Ponemon Institute** - Industry-specific breach costs
- **Sophos State of Ransomware** - Ransomware statistics
- **FBI IC3** - BEC and fraud data

### Compliance Resources
- **HHS Breach Portal** - Healthcare breaches
- **PCI SSC** - Payment card breach data
- **State AG Offices** - Breach notification data

### How to Use
1. Find your industry report
2. Extract frequency (% breached annually)
3. Extract severity (median/average cost)
4. Convert to CRML parameters
5. Document your sources in meta section

---

## Next Steps

- **[Writing CRML](../writing-crml.md)** - Learn to create custom models
- **[Understanding Parameters](../understanding-parameters.md)** - Deep dive on distributions
- **[FAQ](../faq.md)** - Common questions
