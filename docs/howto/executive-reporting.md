# How to Present Results to Executives

A practical guide for communicating CRML results to non-technical stakeholders.

## The Executive Summary Formula

Executives need three numbers:

1. **Expected Annual Loss (EAL)** - "What should we budget?"
2. **VaR 95%** - "What's a bad year?"
3. **VaR 99%** - "What's the worst case?"

## Template: One-Page Executive Summary

```
CYBER RISK ASSESSMENT: [Scenario Name]
Date: [Date]
Prepared by: [Your Name]

EXECUTIVE SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Expected Annual Loss: $220,000
→ Budget this amount annually for [scenario] costs

95% Confidence Level: $450,000  
→ In 95% of years, losses will stay below this amount
→ Only 1 in 20 years will exceed this

Worst-Case Scenario (99%): $650,000
→ Rare but possible (1 in 100 years)
→ Ensure cyber insurance covers at least this amount

RECOMMENDATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Invest $50,000 in Multi-Factor Authentication (MFA)

Expected Risk Reduction: 60% ($132,000/year savings)
Return on Investment: 2.6x
Payback Period: 5 months

METHODOLOGY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Monte Carlo simulation with 10,000 iterations
Based on industry data: Verizon DBIR 2023, IBM Cost of Data Breach Report
Conservative estimates used throughout
```

## Visualization Tips

### 1. Use the Distribution Chart

From the web platform, export the loss distribution chart:

```
[Include histogram showing most losses are small, few are large]
```

**Talking points:**
- "Most years we'll see losses around $200K"
- "Occasionally we'll have a bad year around $400K"
- "Very rarely, we could see $600K+"

### 2. Create a Simple Bar Chart

```
Annual Loss Scenarios
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Expected (Average)    ████████████ $220K
Typical Worst-Case    ████████████████████ $450K  
Extreme Scenario      ██████████████████████████ $650K
```

### 3. Show ROI of Controls

```
Current Risk:         ████████████████████ $500K/year
With MFA:             ████████ $200K/year
Control Cost:         ██ $50K/year
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Net Benefit:          ██████ $250K/year
```

## Common Executive Questions

### "How accurate is this?"

**Good answer:**
> "These estimates are based on industry data from Verizon and IBM, covering thousands of real breaches. We use conservative assumptions, so actual losses may be lower. The methodology is the same used by insurance companies and banks."

**Avoid:**
> "It's a Monte Carlo simulation using Poisson and Lognormal distributions..."

### "Why should I trust these numbers?"

**Good answer:**
> "Three reasons:
> 1. Based on real breach data from 10,000+ companies
> 2. Uses the same methods as cyber insurance pricing
> 3. We can adjust as we track our actual incidents"

### "What if we do nothing?"

**Good answer:**
> "Based on this analysis, we're likely to spend $220K per year on average dealing with [scenario]. That's $1.1M over 5 years. Investing $50K now reduces that to $400K over 5 years - saving $700K."

### "Can we just buy insurance?"

**Good answer:**
> "Insurance is part of the solution. Based on this analysis, we need coverage for at least $650K (our 99th percentile). However, insurance won't cover everything - deductibles, reputation damage, and operational disruption still cost us. Prevention is cheaper than insurance claims."

## Board Presentation Template

### Slide 1: The Problem

```
CYBER RISK: PHISHING ATTACKS

Current State:
• 500 employees with email access
• 10% click rate (industry average)
• ~50 incidents per year expected
• Average cost: $22,000 per incident

Annual Impact: $220,000
```

### Slide 2: The Numbers

```
FINANCIAL IMPACT ANALYSIS

Expected Annual Loss:     $220,000
  → Budget for this amount

95% Confidence:           $450,000
  → "Bad year" scenario

99% Worst-Case:           $650,000
  → Ensure insurance coverage

Methodology: Monte Carlo simulation, 10,000 iterations
Data Source: Verizon DBIR 2023, KnowBe4 Phishing Benchmarks
```

### Slide 3: The Solution

```
RECOMMENDATION: IMPLEMENT MFA

Investment:               $50,000/year
Risk Reduction:           60% (industry proven)
New Expected Loss:        $88,000/year

Annual Savings:           $132,000
ROI:                      2.6x
Payback Period:           5 months

Additional Benefits:
• Compliance (SOC 2, ISO 27001)
• Customer trust
• Reduced insurance premiums
```

### Slide 4: The Ask

```
DECISION REQUIRED

Option A: Implement MFA
• Cost: $50K
• Saves: $132K/year
• Reduces risk by 60%

Option B: Accept Risk
• Cost: $220K/year (expected)
• Up to $650K in bad years
• Compliance concerns

Recommendation: Option A
Timeline: 90 days to implement
Next Steps: Approve budget, select vendor
```

## Email Template

```
Subject: Cyber Risk Assessment - Phishing Attacks

[Executive Name],

I've completed a quantitative risk assessment for phishing attacks. Here are the key findings:

FINANCIAL IMPACT
• Expected annual loss: $220,000
• Worst-case scenario: $650,000 (1 in 100 years)

RECOMMENDATION
Invest $50,000 in Multi-Factor Authentication
• Reduces risk by 60%
• Saves $132,000 per year
• 2.6x return on investment
• Payback in 5 months

NEXT STEPS
• Review full report (attached)
• Approve $50K budget
• Select MFA vendor

This analysis is based on industry data from Verizon and IBM, covering thousands of real breaches. Happy to discuss further.

[Your Name]
```

## Dos and Don'ts

### ✅ DO:

- **Use dollar amounts** - Executives think in budget terms
- **Show ROI** - Compare cost of controls to risk reduction
- **Be conservative** - Better to overestimate risk
- **Provide options** - Give them choices with clear trade-offs
- **Use analogies** - "Like car insurance for cyber risk"
- **Include sources** - "Based on Verizon DBIR data"

### ❌ DON'T:

- **Use jargon** - No "Poisson distributions" or "Monte Carlo"
- **Overwhelm with data** - Stick to 3 key numbers
- **Be vague** - "Significant risk" → "$220K annual loss"
- **Forget the ask** - Always end with clear recommendation
- **Ignore context** - Relate to business goals/compliance

## Follow-Up Materials

### Detailed Report (for those who ask)

```
APPENDIX: METHODOLOGY

Model Parameters:
• Assets: 500 employees
• Frequency: 10% annual click rate (Poisson distribution)
• Severity: $22K median loss (Lognormal distribution)
• Simulation: 10,000 Monte Carlo iterations

Data Sources:
• Verizon DBIR 2023: Phishing statistics
• KnowBe4: Industry click rates
• IBM Cost of Data Breach: Incident costs

Assumptions:
• All employees have equal risk
• Losses include: investigation, remediation, downtime
• Conservative estimates used throughout

Validation:
• Results align with industry benchmarks
• Sensitivity analysis performed
• Reviewed by [Security Team/Auditor]
```

## Measuring Success

After presenting, track:

1. **Decision made?** (Yes/No/Deferred)
2. **Budget approved?** (Full/Partial/None)
3. **Timeline set?** (Date)
4. **Follow-up questions?** (List for FAQ)

Update your presentation based on feedback!

---

## Tools

**Generate executive summary:**
```bash
crml simulate model.yaml --format json | \
  python generate-executive-summary.py > summary.txt
```

**Export charts:**
- Use web platform at http://localhost:3000/simulation
- Run simulation
- Right-click chart → "Save image as..."

**Create comparison:**
```bash
# Before controls
crml simulate baseline.yaml > before.json

# After controls  
crml simulate with-controls.yaml > after.json

# Generate comparison
python compare-scenarios.py before.json after.json > comparison.txt
```

---

## Next Steps

- **[FAQ](../faq.md)** - Answers to common questions
- **[Writing CRML](../writing-crml.md)** - Create your own models
- **[Industry Examples](../examples/by-industry.md)** - Real-world scenarios
