# Control Effectiveness Modeling Guide

## Overview

Control effectiveness modeling in CRML allows you to quantify how security controls reduce cyber risk. This guide explains how to model preventive, detective, and recovery controls with realistic parameters.

---

## Quick Start

### Basic Example

```yaml
crml: "1.1"
meta:
  name: "phishing-with-controls"

model:
  frequency:
    model: poisson
    parameters:
      lambda: 0.20  # 20% baseline probability
  
  controls:
    layers:
      - name: "email_security"
        controls:
          - id: "email_filtering"
            type: "preventive"
            effectiveness: 0.85  # Blocks 85% of phishing emails
            coverage: 1.0        # Covers all users
            reliability: 0.95    # 95% uptime
  
  severity:
    model: lognormal
    parameters:
      median: "50 000"
      sigma: 1.2
```

**Result:** Risk reduced from 20% to ~3% (85% reduction)

---

## Control Parameters

### Required Parameters

#### `id` (string)
Unique identifier for the control.

**Examples:** `"email_filtering"`, `"edr"`, `"mfa"`, `"immutable_backups"`

#### `type` (string)
Control category based on function.

**Valid types:**
- `preventive` - Stops attacks before they occur
- `detective` - Identifies attacks in progress
- `corrective` - Fixes vulnerabilities
- `recovery` - Restores after incidents
- `deterrent` - Discourages attackers
- `compensating` - Alternative protection

#### `effectiveness` (0-1)
How well the control works when functioning properly.

**Guidelines:**
- `0.95-1.0` - Highly effective (e.g., immutable backups, air-gapped systems)
- `0.80-0.95` - Very effective (e.g., MFA, EDR, email filtering)
- `0.60-0.80` - Moderately effective (e.g., security awareness, basic AV)
- `0.40-0.60` - Somewhat effective (e.g., password policies, basic monitoring)
- `0.0-0.40` - Limited effectiveness

**Examples:**
```yaml
effectiveness: 0.90  # Email filtering blocks 90% of phishing
effectiveness: 0.75  # EDR detects 75% of malware
effectiveness: 0.60  # Security training reduces clicks by 60%
```

### Optional Parameters

#### `coverage` (0-1, default: 1.0)
What percentage of assets/attack surface the control covers.

**Examples:**
```yaml
coverage: 1.0   # All users/systems
coverage: 0.95  # 95% of endpoints
coverage: 0.80  # 80% of network segmented
```

#### `reliability` (0-1, default: 1.0)
How reliably the control functions (uptime, accuracy).

**Examples:**
```yaml
reliability: 0.99  # 99% uptime
reliability: 0.95  # 95% detection accuracy
reliability: 0.90  # 90% of time functioning
```

#### `cost` (number)
Annual cost in base currency for ROI calculations.

```yaml
cost: 50000
currency: USD
```

---

## Mathematical Model

### Single Control

```
Effective Reduction = effectiveness × coverage × reliability
```

**Example:**
```yaml
effectiveness: 0.90
coverage: 0.95
reliability: 0.98
```
Reduction = 0.90 × 0.95 × 0.98 = **0.838 (83.8%)**

### Multiple Controls (Defense in Depth)

Controls combine multiplicatively:

```
P(breach) = P₀ × (1 - R₁) × (1 - R₂) × ... × (1 - Rₙ)
```

Where:
- P₀ = baseline probability
- Rᵢ = reduction from control i

**Example:**
```yaml
# Baseline: 15% probability
# Control 1: 85% reduction
# Control 2: 70% reduction

P(breach) = 0.15 × (1 - 0.85) × (1 - 0.70)
          = 0.15 × 0.15 × 0.30
          = 0.00675 (0.675%)

Risk reduction = (0.15 - 0.00675) / 0.15 = 95.5%
```

---

## Control Layers

Organize controls by function for clarity:

```yaml
controls:
  layers:
    - name: "preventive_controls"
      description: "Stop attacks before they occur"
      controls:
        - id: "email_filtering"
          type: "preventive"
          effectiveness: 0.90
        
        - id: "mfa"
          type: "preventive"
          effectiveness: 0.95
    
    - name: "detective_controls"
      description: "Identify attacks in progress"
      controls:
        - id: "edr"
          type: "detective"
          effectiveness: 0.80
        
        - id: "siem"
          type: "detective"
          effectiveness: 0.70
    
    - name: "recovery_controls"
      description: "Restore after incidents"
      controls:
        - id: "immutable_backups"
          type: "recovery"
          effectiveness: 0.95
```

---

## Control Dependencies

When controls are correlated (may fail together or provide overlapping protection):

```yaml
controls:
  layers:
    - name: "endpoint_protection"
      controls:
        - id: "edr"
          type: "detective"
          effectiveness: 0.80
        
        - id: "antivirus"
          type: "preventive"
          effectiveness: 0.70
  
  dependencies:
    - controls: ["edr", "antivirus"]
      correlation: 0.5  # Both target endpoint threats
```

**Correlation values:**
- `0.0` - Independent (no overlap)
- `0.3` - Low correlation (some overlap)
- `0.5` - Moderate correlation
- `0.7` - High correlation
- `1.0` - Perfectly correlated (complete overlap)

---

## Common Control Patterns

### Email Security

```yaml
- name: "email_security"
  controls:
    - id: "email_filtering"
      type: "preventive"
      effectiveness: 0.90
      coverage: 1.0
      reliability: 0.95
      cost: 50000
    
    - id: "security_awareness_training"
      type: "preventive"
      effectiveness: 0.60
      coverage: 0.95
      reliability: 0.90
      cost: 25000

dependencies:
  - controls: ["email_filtering", "security_awareness_training"]
    correlation: 0.4  # Both target email threats
```

### Endpoint Protection

```yaml
- name: "endpoint_protection"
  controls:
    - id: "edr"
      type: "detective"
      effectiveness: 0.80
      coverage: 0.98
      reliability: 0.92
      cost: 120000
    
    - id: "application_whitelisting"
      type: "preventive"
      effectiveness: 0.85
      coverage: 0.90
      reliability: 0.95
      cost: 40000
```

### Network Defense

```yaml
- name: "network_defense"
  controls:
    - id: "network_segmentation"
      type: "preventive"
      effectiveness: 0.70
      coverage: 0.85
      reliability: 0.99
      cost: 80000
    
    - id: "ids_ips"
      type: "detective"
      effectiveness: 0.65
      coverage: 1.0
      reliability: 0.90
      cost: 60000
```

### Backup & Recovery

```yaml
- name: "backup_recovery"
  controls:
    - id: "immutable_backups"
      type: "recovery"
      effectiveness: 0.95
      coverage: 0.98
      reliability: 0.99
      cost: 75000
    
    - id: "disaster_recovery_plan"
      type: "recovery"
      effectiveness: 0.85
      coverage: 1.0
      reliability: 0.95
      cost: 30000
```

---

## Best Practices

### 1. Use Realistic Effectiveness Values

❌ **Don't:**
```yaml
effectiveness: 0.99  # Unrealistically high for most controls
```

✅ **Do:**
```yaml
effectiveness: 0.85  # Realistic for good email filtering
```

### 2. Model Defense in Depth

❌ **Don't:** Rely on single control
```yaml
controls:
  layers:
    - name: "security"
      controls:
        - id: "firewall"
          effectiveness: 0.95
```

✅ **Do:** Layer multiple controls
```yaml
controls:
  layers:
    - name: "perimeter"
      controls:
        - id: "firewall"
          effectiveness: 0.70
    
    - name: "endpoint"
      controls:
        - id: "edr"
          effectiveness: 0.80
    
    - name: "recovery"
      controls:
        - id: "backups"
          effectiveness: 0.95
```

### 3. Account for Coverage Gaps

```yaml
- id: "edr"
  effectiveness: 0.80
  coverage: 0.95  # 5% of endpoints not covered
  reliability: 0.92
```

### 4. Include Costs for ROI Analysis

```yaml
- id: "email_filtering"
  effectiveness: 0.90
  cost: 50000
  currency: USD
```

### 5. Model Control Dependencies

```yaml
dependencies:
  - controls: ["email_filtering", "security_awareness"]
    correlation: 0.4  # Both target email-based attacks
```

---

## Calibrating Control Parameters

### From Vendor Data

Many security vendors provide effectiveness metrics:

**Email Security:**
- Proofpoint: 99.99% spam catch rate → `effectiveness: 0.9999`
- Mimecast: 99.9% phishing detection → `effectiveness: 0.999`

**Endpoint Protection:**
- CrowdStrike: 99% malware detection → `effectiveness: 0.99`
- SentinelOne: 97% threat prevention → `effectiveness: 0.97`

**Note:** Vendor claims are often optimistic. Consider using 80-90% of claimed effectiveness.

### From Historical Data

If you have incident data:

```
Effectiveness = (Attacks Blocked) / (Total Attacks)
```

**Example:**
- Total phishing attempts: 1,000
- Blocked by email filter: 850
- Effectiveness: 850/1000 = **0.85**

### From Industry Benchmarks

**NIST, SANS, CIS** provide control effectiveness guidance:

- MFA: 90-99% effective against credential attacks
- Email filtering: 85-95% effective against phishing
- EDR: 75-85% effective against malware
- Network segmentation: 60-80% effective against lateral movement

---

## Interpreting Results

### Simulation Output

```
CONTROL EFFECTIVENESS RESULTS:
------------------------------------------------------------
Baseline Lambda (no controls):    0.150000
Effective Lambda (with controls): 0.034602
Risk Reduction:                   76.9%

INDIVIDUAL CONTROLS:
------------------------------------------------------------
email_filtering (preventive)
  Effectiveness: 90%, Coverage: 100%, Reliability: 95%
  Combined Reduction: 85.5%

edr (detective)
  Effectiveness: 80%, Coverage: 98%, Reliability: 92%
  Combined Reduction: 72.1%
```

### Key Metrics

**Lambda Baseline:** Probability without controls  
**Lambda Effective:** Probability with controls  
**Risk Reduction:** Percentage decrease in probability  
**Combined Reduction:** Per-control effective reduction (E × C × R)

---

## Troubleshooting

### Warning: Unrealistic Risk Reduction

```
⚠️  Warning: Total risk reduction is 99.8%. This is extremely high 
    and may be unrealistic.
```

**Cause:** Controls are too effective or too many layers

**Solution:**
- Review effectiveness values (should be 0.6-0.9 for most controls)
- Reduce number of controls
- Add control dependencies to model overlap

### Controls Not Applied

**Check:**
1. Frequency model is `poisson` (controls only work with Poisson currently)
2. Controls block is properly formatted
3. All required fields present (`id`, `type`, `effectiveness`)

---

## Examples

See working examples in `spec/examples/`:
- [ransomware-with-controls.yaml](/spec/examples/ransomware-with-controls.yaml) - Comprehensive ransomware defense

---

## Advanced Topics

### Control ROI Calculation

```python
ROI = (Risk Reduction - Control Cost) / Control Cost
```

Enable in output:
```yaml
output:
  control_analysis:
    show_control_roi: true
```

### Time-Varying Effectiveness

Future feature: Model control degradation over time

```yaml
# Planned for future release
controls:
  - id: "signature_based_av"
    effectiveness: 0.80
    degradation:
      rate: 0.05  # 5% annual degradation
```

---

## References

- CRML Specification: [crml-1.1.md](/spec/crml-1.1.md)
- NIST Cybersecurity Framework: Control effectiveness guidance
- FAIR Model: Control strength estimation
- CIS Controls: Implementation benchmarks
