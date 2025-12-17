# Control Effectiveness Modeling

This guide explains how to represent security controls in CRML and how the reference engine applies them during simulation.

Notes:
- Controls are part of the CRML document model.
- The reference engine (`crml_engine`) applies control effectiveness when running simulations.
- In the current reference engine, control effectiveness is applied to **Poisson** frequency via an adjusted effective `lambda`.

---

## Overview

Control effectiveness modeling allows you to:

- **Quantify risk reduction** from security controls
- **Model defense-in-depth** with multiple layered controls
- **Calculate ROI** for security investments
- **Optimize control portfolios** based on effectiveness and cost
- **Account for real-world factors** like coverage gaps and reliability

---

## Quick Start

### Basic Control

```yaml
model:
  frequency:
    model: poisson
    parameters:
      lambda: 0.15  # Baseline threat-event rate (threat likelihood) for the chosen basis
  
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

---

## Control Parameters

### Required Parameters

#### `id` (string)
Unique identifier for the control.

**Examples:** `"email_filtering"`, `"edr"`, `"mfa"`, `"immutable_backups"`

#### `type` (string)
Control category. Affects how the control is applied.

**Options:**
- `preventive` - Stops attacks before they occur (firewalls, email filtering, MFA)
- `detective` - Identifies attacks in progress (EDR, SIEM, IDS)
- `recovery` - Restores after incidents (backups, disaster recovery)
- `corrective` - Fixes vulnerabilities (patch management)
- `deterrent` - Discourages attacks (security awareness)
- `compensating` - Alternative controls

#### `effectiveness` (0-1)
How well the control works when functioning properly.

**Guidelines:**
- `0.95-1.0` - Highly effective (immutable backups, air-gapped systems)
- `0.80-0.95` - Very effective (MFA, EDR, email filtering)
- `0.60-0.80` - Moderately effective (security awareness, basic firewalls)
- `0.40-0.60` - Limited effectiveness (antivirus, signature-based detection)
- `<0.40` - Low effectiveness (rarely used)

### Optional Parameters

#### `coverage` (0-1, default: 1.0)
Percentage of assets/users covered by the control.

**Examples:**
- `1.0` - All users/assets covered
- `0.98` - 98% of endpoints have EDR
- `0.85` - 85% of network is segmented

#### `reliability` (0-1, default: 1.0)
How reliably the control functions (uptime, accuracy).

**Examples:**
- `0.99` - 99% uptime
- `0.95` - 95% detection accuracy
- `0.90` - 90% effectiveness retention after training

#### `cost` (number)
Annual cost of the control for ROI calculations.

**Example:** `50000` for $50K/year

#### `currency` (string)
Currency for the cost.

**Example:** `USD`, `EUR`, `GBP`

---

## Mathematical Model

### Single Control

The effective reduction from a single control is:

```
Reduction = effectiveness × coverage × reliability
```

**Example:**
```yaml
effectiveness: 0.90
coverage: 0.98
reliability: 0.95
```

Reduction = 0.90 × 0.98 × 0.95 = **0.838** (83.8%)

### Multiple Controls (Defense-in-Depth)

When multiple controls are applied in series, the probability of breach is:

```
P(breach) = P₀ × ∏ᵢ (1 - Rᵢ)
```

Where:
- `P₀` = Baseline probability (lambda)
- `Rᵢ` = Reduction from control i

**Example:**
```yaml
controls:
  layers:
    - name: "email"
      controls:
        - id: "filtering"
          effectiveness: 0.90  # R₁ = 0.90
    
    - name: "endpoint"
      controls:
        - id: "edr"
          effectiveness: 0.80  # R₂ = 0.80
```

Calculation:
```
P(breach) = 0.15 × (1 - 0.90) × (1 - 0.80)
          = 0.15 × 0.10 × 0.20
          = 0.003 (0.3%)
```

**Risk Reduction:** 98% (from 15% to 0.3%)

---

## Control Layers

Organize controls into logical layers:

```yaml
controls:
  layers:
    - name: "perimeter_defense"
      description: "External-facing security"
      controls:
        - id: "firewall"
          type: "preventive"
          effectiveness: 0.70
        
        - id: "waf"
          type: "preventive"
          effectiveness: 0.85
    
    - name: "endpoint_protection"
      description: "Device-level security"
      controls:
        - id: "edr"
          type: "detective"
          effectiveness: 0.80
        
        - id: "application_whitelisting"
          type: "preventive"
          effectiveness: 0.85
    
    - name: "data_protection"
      description: "Data-level controls"
      controls:
        - id: "encryption"
          type: "preventive"
          effectiveness: 0.95
        
        - id: "dlp"
          type: "detective"
          effectiveness: 0.75
```

---

## Control Dependencies

When controls overlap or may fail together, model their correlation:

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
- `0.0` - Completely independent
- `0.3-0.5` - Some overlap (same threat vector)
- `0.7-0.9` - High overlap (same technology)
- `1.0` - Completely dependent (same control)

**Effect:** Reduces combined effectiveness to account for overlap.

---

## Complete Example

```yaml
crml: "1.1"

meta:
  name: "ransomware-defense-in-depth"
  description: "Layered ransomware protection"

model:
  frequency:
    model: poisson
    parameters:
      lambda: 0.15  # 15% baseline
  
  controls:
    layers:
      - name: "email_security"
        controls:
          - id: "email_filtering"
            type: "preventive"
            effectiveness: 0.90
            coverage: 1.0
            reliability: 0.95
            cost: 50000
            currency: USD
          
          - id: "security_awareness"
            type: "preventive"
            effectiveness: 0.60
            coverage: 0.95
            reliability: 0.90
            cost: 25000
            currency: USD
      
      - name: "endpoint_protection"
        controls:
          - id: "edr"
            type: "detective"
            effectiveness: 0.80
            coverage: 0.98
            reliability: 0.92
            cost: 120000
            currency: USD
          
          - id: "application_whitelisting"
            type: "preventive"
            effectiveness: 0.85
            coverage: 0.90
            reliability: 0.95
            cost: 40000
            currency: USD
      
      - name: "network_defense"
        controls:
          - id: "network_segmentation"
            type: "preventive"
            effectiveness: 0.70
            coverage: 0.85
            reliability: 0.99
            cost: 80000
            currency: USD
      
      - name: "backup_recovery"
        controls:
          - id: "immutable_backups"
            type: "recovery"
            effectiveness: 0.95
            coverage: 0.98
            reliability: 0.99
            cost: 75000
            currency: USD
    
    dependencies:
      - controls: ["email_filtering", "security_awareness"]
        correlation: 0.4  # Both target email attacks
      
      - controls: ["edr", "application_whitelisting"]
        correlation: 0.3  # Some endpoint overlap
  
  severity:
    model: lognormal
    parameters:
      median: "700 000"
      currency: USD
      sigma: 1.8
```

**Results:**
```
CONTROL EFFECTIVENESS RESULTS
==============================
Baseline Lambda (no controls):    0.150000
Effective Lambda (with controls): 0.034602
Risk Reduction:                   76.9%

Individual Control Contributions:
- email_filtering:           85.5% reduction
- security_awareness:        51.3% reduction
- edr:                       72.5% reduction
- application_whitelisting:  72.7% reduction
- network_segmentation:      58.7% reduction
- immutable_backups:         92.2% reduction

Total Control Cost: $390,000/year
Expected Annual Loss (with controls): $24,221
ROI: 62% reduction in loss per dollar spent
```

---

## Best Practices

### ✅ Do

- **Use realistic effectiveness values** (0.6-0.9 for most controls)
- **Layer multiple control types** (preventive + detective + recovery)
- **Account for coverage gaps** (not all assets may be protected)
- **Include reliability factors** (controls aren't 100% reliable)
- **Model dependencies** when controls overlap
- **Include costs** for ROI analysis

### ❌ Don't

- **Use unrealistically high effectiveness** (>0.95 for most controls)
- **Rely on a single control** (no defense-in-depth)
- **Ignore coverage and reliability** (assume perfect deployment)
- **Forget dependencies** (controls often overlap)
- **Neglect costs** (can't optimize without cost data)

---

## Calibration Guidance

### From Vendor Data

Use vendor-published effectiveness rates:

```yaml
- id: "email_filtering"
  effectiveness: 0.92  # Vendor claims 92% detection rate
  reliability: 0.95    # 95% uptime SLA
```

### From Historical Incidents

Calculate from past incidents:

```
effectiveness = 1 - (incidents_with_control / total_incidents)
```

**Example:** 100 total incidents, 8 occurred despite email filtering:
```
effectiveness = 1 - (8/100) = 0.92
```

### From Industry Benchmarks

Use industry reports (Verizon DBIR, Ponemon, etc.):

- **Email filtering:** 0.85-0.95
- **EDR:** 0.75-0.85
- **MFA:** 0.90-0.99
- **Security awareness:** 0.50-0.70
- **Network segmentation:** 0.60-0.80
- **Immutable backups:** 0.95-0.99

---

## ROI Calculations

CRML automatically calculates ROI for controls:

```
ROI = (Baseline EAL - Effective EAL) / Total Control Cost
```

**Example:**
- Baseline EAL: $100,000
- Effective EAL: $24,000
- Control Cost: $390,000/year

```
ROI = ($100,000 - $24,000) / $390,000 = 0.195 (19.5%)
```

**Interpretation:** For every dollar spent on controls, you reduce loss by $0.195.

---

## Troubleshooting

### Warning: "Unrealistic risk reduction"

**Cause:** Combined controls reduce risk by >99%.

**Solution:** 
- Review effectiveness values (may be too high)
- Check for missing dependencies
- Verify baseline lambda is realistic

### Controls not reducing risk

**Cause:** Controls may not be applied to the right model component.

**Solution:**
- Controls currently only apply to frequency (lambda)
- Ensure `frequency` model is specified
- Check that control IDs are unique

---

## Next Steps

- **[Examples](Examples)** - See more control modeling examples
- **[API Reference](API-Reference)** - Use controls in Python code

---

**See Also:**
- [CRML 1.1 Specification](Reference/CRML-1.1)
- [CRML Schema](Reference/CRML-Schema)
