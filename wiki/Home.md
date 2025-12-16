# CRML Documentation

CRML (Cyber Risk Modeling Language) is a declarative YAML/JSON format for describing cyber risk models.

This repository is split into two Python packages:

- `crml_lang` (**language/spec**): models + schema + validation + YAML IO
- `crml_engine` (**reference engine**): CLI + simulation/runtime (depends on `crml_lang`)

## Quick links

- Language overview: [Language/Overview](Language/Overview)
- Engine overview: [Engine/Overview](Engine/Overview)
- Quickstart (CLI): [Quickstart](Quickstart)
- Examples: [Examples](Examples)
- CRML 1.1 spec: [Reference/CRML-1.1](Reference/CRML-1.1)

## Install

If you want the **CLI** (`crml validate`, `crml simulate`):

```bash
pip install crml-engine
```

If you only want the **language library** in Python:

```bash
pip install crml-lang
```

## Minimal example

```yaml
crml: "1.1"

meta:
  name: "ransomware-risk"

model:
  frequency:
    model: poisson
    parameters:
      lambda: 0.15

  severity:
    model: lognormal
    parameters:
      median: "500 000"
      currency: USD
      sigma: 1.5
```

## Contributing

See [Contributing](Contributing).
