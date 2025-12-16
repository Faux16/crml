# Welcome to CRML Wiki

**Cyber Risk Modeling Language (CRML)** is an open, declarative language for expressing cyber risk models with Monte Carlo simulation and control effectiveness modeling.

[![PyPI version](https://badge.fury.io/py/crml-lang.svg)](https://pypi.org/project/crml-lang/)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🚀 Quick Links

- **[Getting Started](Getting-Started)** - Install and run your first simulation
- **[Roadmap](Roadmap)** - Future features and development timeline
- **[Control Effectiveness Guide](Control-Effectiveness)** - Model security controls
- **[Examples](Examples)** - Real-world risk models
- **[API Reference](API-Reference)** - Python API documentation

---

## ✨ What is CRML?

CRML enables you to:

- **Model cyber risks** using frequency and severity distributions
- **Quantify control effectiveness** with defense-in-depth calculations
- **Run Monte Carlo simulations** to calculate Expected Annual Loss (EAL) and Value at Risk (VaR)
- **Support multiple currencies** with automatic conversion
- **Auto-calibrate** distributions from historical loss data
- **Validate models** with strict JSON Schema validation

---

## 📦 Installation

```bash
pip install crml-lang
```

---

## 🎯 Quick Example

```yaml
crml: "1.1"

meta:
  name: "ransomware-risk"
  description: "Ransomware risk with email filtering control"

model:
  frequency:
    model: poisson
    parameters:
      lambda: 0.15  # 15% annual probability
  
  controls:
    layers:
      - name: "email_security"
        controls:
          - id: "email_filtering"
            type: "preventive"
            effectiveness: 0.90  # Blocks 90% of attacks
            coverage: 1.0
            reliability: 0.95
  
  severity:
    model: lognormal
    parameters:
      median: "500 000"
      currency: USD
      sigma: 1.5
```

**Result:** Risk reduced from 15% to ~1.5% (90% reduction!)

---

## 🛡️ New in v1.2.0: Control Effectiveness

Model how security controls reduce cyber risk:

- **Preventive controls** - Stop attacks before they occur
- **Detective controls** - Identify attacks in progress
- **Recovery controls** - Restore after incidents
- **Defense-in-depth** - Layer multiple controls
- **ROI calculations** - Quantify security investments

[Learn more →](Control-Effectiveness)

---

## 📚 Documentation

### Getting Started
- [Installation](Getting-Started#installation)
- [Your First Model](Getting-Started#your-first-model)
- [Running Simulations](Getting-Started#running-simulations)

### Guides
- [Writing CRML Models](Writing-CRML-Models)
- [Control Effectiveness](Control-Effectiveness)
- [Multi-Currency Support](Multi-Currency-Support)
- [Auto-Calibration](Auto-Calibration)

### Reference
- [CRML Specification](https://github.com/Faux16/crml/blob/main/spec/crml-1.1.md)
- [API Reference](API-Reference)
- [Examples](Examples)

---

## 🗺️ Roadmap

See our [Roadmap](Roadmap) for upcoming features:

- ✅ **v1.2.0** - Control Effectiveness Modeling (Released)
- 🚧 **v1.3.0** - Attack Chain Modeling (In Progress)
- 📋 **v1.4.0** - Threat Actor Modeling (Planned)
- 📋 **v2.0.0** - Bayesian Inference with MCMC (Future)

---

## 🤝 Contributing

We welcome contributions! See our [Contributing Guide](Contributing) for:

- Code contributions
- Documentation improvements
- Bug reports
- Feature requests

---

## 💬 Community

- **GitHub Issues:** [Report bugs or request features](https://github.com/Faux16/crml/issues)
- **Discussions:** [Ask questions and share models](https://github.com/Faux16/crml/discussions)
- **PyPI:** [crml-lang package](https://pypi.org/project/crml-lang/)

---

## 📄 License

CRML is released under the [MIT License](https://github.com/Faux16/crml/blob/main/LICENSE).

---

**Maintained by [Zeron Research Labs](https://zeron.one)**
