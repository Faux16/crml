# CRML — Cyber Risk Modeling Language

**Version:** 1.0  
**Maintained by:** Zeron Research Labs  

CRML is an open, declarative, implementation-agnostic language for
expressing cyber risk models, telemetry mappings, simulation pipelines,
dependencies, and output requirements.

CRML is designed for:

- Bayesian cyber risk models (QBER, MCMC-based)
- FAIR-style Monte Carlo engines
- Insurance actuarial risk systems
- Enterprise cyber risk quantification platforms
- Regulatory or audit-ready risk engines

## Repository Layout

- `spec/` — CRML 1.0 specification, JSON Schema, and example models
- `tools/` — Validator and CLI utilities
- `docs/` — Roadmap and diagrams

## Quick Start

1. Install dependencies:

```bash
pip install pyyaml jsonschema
```

2. Validate a CRML file:

```bash
python tools/validator/crml_validator.py spec/examples/qber-enterprise.yaml
```

## License

MIT License — see `LICENSE`.
