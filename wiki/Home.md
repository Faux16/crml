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
- Scenario schema + docs: [Language/Overview](Language/Overview)

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
crml_scenario: "1.0"

meta:
  name: "ransomware-risk"

scenario:
  frequency:
    basis: per_organization_per_year
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
