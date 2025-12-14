# CRML — Cyber Risk Modeling Language

[![PyPI version](https://badge.fury.io/py/crml-lang.svg)](https://badge.fury.io/py/crml-lang)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Version:** 1.1  
**Maintained by:** Zeron Research Labs  

CRML is an open, declarative, implementation-agnostic language for expressing cyber risk models, telemetry mappings, simulation pipelines, dependencies, and output requirements.

## 🎯 Use Cases

CRML is designed for:

- **Bayesian cyber risk models** (QBER, MCMC-based)
- **FAIR-style Monte Carlo engines**
- **Insurance actuarial risk systems**
- **Enterprise cyber risk quantification platforms**
- **Regulatory or audit-ready risk engines**

## 📦 Installation

Install CRML from PyPI:

```bash
pip install crml-lang
```

## 🚀 Quick Start

### Validate a CRML File

```bash
crml validate path/to/your/model.yaml
```

### Example

```bash
crml validate spec/examples/qber-enterprise.yaml
```

Output:
```
[OK] spec/examples/qber-enterprise.yaml is a valid CRML 1.1 document.
```

## 📁 Repository Layout

- **`spec/`** — CRML 1.1 specification, JSON Schema, and example models
- **`src/crml/`** — Python package source code (validator, CLI)
- **`tools/`** — Legacy validator and CLI utilities
- **`docs/`** — Documentation, roadmap, and diagrams

## 🛠️ Development

### Install from Source

```bash
git clone https://github.com/Faux16/crml.git
cd crml
pip install -e .
```

### Run Validator Directly

```bash
python tools/validator/crml_validator.py spec/examples/qber-enterprise.yaml
```

## 📖 Documentation

For detailed documentation, examples, and the full specification, visit the `docs/` directory or check out the [specification](spec/crml-1.1.md).

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## 📄 License

MIT License — see [`LICENSE`](LICENSE) for details.

## 🔗 Links

- **PyPI Package:** https://pypi.org/project/crml-lang/
- **GitHub Repository:** https://github.com/Faux16/crml
- **Specification:** [CRML 1.1](spec/crml-1.1.md)

---

**Maintained by Zeron Research Labs** | [Website](https://zeron.one) | [Contact](mailto:research@zeron.one)

