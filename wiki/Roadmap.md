# Roadmap

This documentation set intentionally avoids embedding forward-looking roadmaps.

For current capabilities, use:

- the language and engine pages in the navigation
- the package changelogs for historical changes

For discussions, suggestions, ideas and work tracking, use the repository issue tracker.

This information is just being kept here for retention reasons and might be deleted later:

## Draft (In Progress)

### v1.3.0 - Attack Chain Modeling

**Status:** Draft

**Priority:** High

Model multi-stage cyber attacks with sequential probabilities and control impact at each stage.

**Planned Features:**
- Attack chain / kill chain modeling
- Stage-by-stage probability calculations
- Control effectiveness per stage
- Branching attack paths
- Time-to-compromise modeling

**Example:**
```yaml
attack_chain:
  stages:
    - name: "initial_access"
      probability: 0.15
      controls: ["email_filtering", "mfa"]
    
    - name: "lateral_movement"
      probability: 0.40
      controls: ["network_segmentation", "edr"]
    
    - name: "data_exfiltration"
      probability: 0.60
      controls: ["dlp", "monitoring"]
```

**Use Cases:**
- Ransomware attack modeling
- APT scenario analysis
- Incident response planning

**Estimated Effort:** 40-50 hours

---

## Draft (Planned)

### v1.4.0 - Threat Actor Modeling

**Status:** Draft

**Priority:** High

Differentiate risk based on threat actor sophistication, motivation, and tactics.

**Planned Features:**
- Threat actor profiles (nation-state, cybercrime, insider)
- Sophistication levels affecting control effectiveness
- Motivation-based targeting
- TTPs (Tactics, Techniques, Procedures) mapping
- MITRE ATT&CK integration

**Example:**
```yaml
threat_actors:
  - name: "ransomware_gang"
    sophistication: "medium"
    motivation: "financial"
    frequency_multiplier: 1.5
    control_bypass_probability: 0.20
```

**Estimated Effort:** 30-40 hours

---

### v1.5.0 - Data-Driven Calibration

**Status:** Draft

**Priority:** Medium

Automate parameter estimation from historical incident data.

**Planned Features:**
- Maximum Likelihood Estimation (MLE)
- Bayesian parameter inference
- Goodness-of-fit testing
- Confidence intervals
- Data import from CSV/JSON

**Example:**
```yaml
data:
  sources:
    - type: "csv"
      path: "incidents.csv"
      columns:
        date: "incident_date"
        loss: "total_loss"
  
  calibration:
    method: "mle"
    distribution: "lognormal"
```

**Estimated Effort:** 50-60 hours

---

### v1.6.0 - Temporal Dynamics

**Status:** Draft

**Priority:** Medium

Model time-varying parameters for frequency and severity.

**Planned Features:**
- Time-series frequency modeling
- Seasonal patterns
- Trend analysis
- Control degradation over time
- Inflation adjustment for severity

**Example:**
```yaml
temporal:
  frequency:
    trend: "increasing"
    rate: 0.05  # 5% annual increase
    seasonality:
      pattern: "quarterly"
      peaks: [1, 4]  # Q1 and Q4
  
  controls:
    - id: "antivirus"
      degradation_rate: 0.10  # 10% annual degradation
```

**Estimated Effort:** 40-50 hours

---

### v1.7.0 - Vulnerability & Exposure Modeling

**Status:** Draft

**Priority:** Medium

Integrate CVE/CVSS data and asset exposure factors.

**Planned Features:**
- CVE database integration
- CVSS score impact on frequency
- Asset exposure modeling
- Patch management simulation
- Zero-day risk modeling

**Example:**
```yaml
assets:
  - name: "web_servers"
    count: 50
    exposure: "internet_facing"
    vulnerabilities:
      - cve: "CVE-2024-1234"
        cvss: 9.8
        patched: false
```

**Estimated Effort:** 30-40 hours

---

### v1.8.0 - Breach Cost Modeling

**Status:** Draft

**Priority:** Low

Structure severity models around specific breach cost components.

**Planned Features:**
- Detection and escalation costs
- Notification costs
- Legal and regulatory costs
- Business disruption costs
- Reputation damage modeling

**Example:**
```yaml
severity:
  model: "breach_cost"
  components:
    detection:
      median: "50 000"
      sigma: 1.2
    
    notification:
      per_record: 5
      records_at_risk: 100000
    
    legal:
      median: "200 000"
      sigma: 1.8
```

**Estimated Effort:** 25-35 hours

---

### v1.9.0 - Insurance & Risk Transfer

**Status:** 🔮 Research

**Priority:** Medium

Model cyber insurance policies and risk transfer mechanisms.

**Planned Features:**
- Insurance policy modeling
- Deductibles and limits
- Coinsurance percentages
- Aggregate limits
- Premium calculations

**Example:**
```yaml
insurance:
  policy:
    deductible: "100 000"
    limit: "5 000 000"
    coinsurance: 0.20  # 20% coinsurance
    aggregate_limit: "10 000 000"
```

**Estimated Effort:** 30-40 hours

---

## Draft (Future v2.0+)

### v2.0.0 - Bayesian Inference with MCMC

**Status:** 🔮 Research

**Priority:** High

Full uncertainty quantification using Markov Chain Monte Carlo methods.

**Planned Features:**
- MCMC sampling (Metropolis-Hastings, NUTS, HMC)
- Prior distribution specification
- Posterior distribution analysis
- Convergence diagnostics
- Credible intervals

**Example:**
```yaml
pipeline:
  simulation:
    mcmc:
      enabled: true
      algorithm: "nuts"
      iterations: 10000
      burn_in: 1000
      chains: 4
```

**Estimated Effort:** 80-100 hours

---

### v2.1.0 - Portfolio Aggregation

**Status:** 🔮 Research

**Priority:** Medium

Aggregate multiple correlated risk models at enterprise level.

**Planned Features:**
- Multi-scenario aggregation
- Correlation modeling between scenarios
- Portfolio-level VaR
- Diversification benefits
- Concentration risk analysis

**Estimated Effort:** 60-80 hours

---

### v2.2.0 - Advanced Copulas

**Status:** 🔮 Research

**Priority:** Low

Enhanced dependency modeling with advanced copula functions.

**Planned Features:**
- Vine copulas
- Time-varying copulas
- Tail dependency modeling
- Copula selection algorithms

**Estimated Effort:** 40-50 hours

---

## 🎯 Priority Legend

- **High** - Core functionality, high user demand
- **Medium** - Important features, moderate demand
- **Low** - Nice-to-have, specialized use cases

---

## 📊 Release Order

```
✅ v1.2.0 Control Effectiveness
🚧 v1.3.0 Attack Chain Modeling
📋 v1.4.0 Threat Actor Modeling
📋 v1.5.0 Data-Driven Calibration
📋 v1.6.0 Temporal Dynamics
📋 v1.7.0 Vulnerability Modeling
📋 v1.8.0 Breach Cost Modeling
📋 v1.9.0 Insurance Modeling
🔮 v2.0.0 Bayesian Inference
```

---

## 🤝 Contributing

Want to help implement these features?

1. Check the [Issues](https://github.com/Faux16/crml/issues) for open tasks
2. Comment on features you're interested in
3. Submit PRs for roadmap items
4. Suggest new features in [Discussions](https://github.com/Faux16/crml/discussions)

---

## 📝 Notes

- Timeline estimates are subject to change based on community feedback and priorities
- Effort estimates assume experienced Python developer
- Features may be delivered in a different order based on demand
- Breaking changes will follow semantic versioning (major version bumps)

---

**Last Updated:** December 15, 2024
