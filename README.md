# CRML — Cyber Risk Modeling Language

[![crml-lang](https://badge.fury.io/py/crml-lang.svg)](https://pypi.org/project/crml-lang/)
[![crml-engine](https://badge.fury.io/py/crml-engine.svg)](https://pypi.org/project/crml-engine/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Status:** Draft. This project is under heavy development and may change without notice.

CRML is an open, declarative YAML/JSON format for describing cyber risk models, whith a focus on supporting risk quantification engines.

This repository ships two Python packages and a web UI:

- `crml-lang`: language/spec models + schema validation + YAML IO
- `crml-engine`: reference runtime + `crml` CLI (depends on `crml-lang`)
- `web/`: **CRML Studio** — browser UI for validation and simulation (Next.js)

## Installation

If you want the CLI:

```bash
pip install crml-engine
```

If you only want the language library:

```bash
pip install crml-lang
```

## Quick start (CLI)

```bash
crml validate examples/scenarios/qber-enterprise.yaml
crml simulate examples/scenarios/data-breach-simple.yaml --runs 10000
```

## Quick start (Python)

Load and validate:

```python
from crml_lang import CRScenario, validate

scenario = CRScenario.load_from_yaml("examples/scenarios/data-breach-simple.yaml")
report = validate("examples/scenarios/data-breach-simple.yaml", source_kind="path")
print(report.ok)
```

Run a simulation:

```python
from crml_engine.runtime import run_simulation

result = run_simulation("examples/scenarios/data-breach-simple.yaml", n_runs=10000)
print(result.metrics.eal)
```

## Repository layout

- `crml_lang/` — language/spec package
- `crml_engine/` — reference engine package
- `web/` — web UI (Next.js)
- `examples/` — example CRML YAML models and FX config
- `wiki/` — documentation source (MkDocs)

## CRML Studio

CRML Studio lives in `web/`.

Run it locally:

```bash
pip install crml-engine
cd web
npm install
npm run dev
```

Open http://localhost:3000

## Screenshots

![Simulation](images/simulation.png)

![Validator](images/validator.png)

## Documentation

See the docs under `wiki/`.

Current document types:

- Scenario documents: `crml_scenario: "1.0"` with top-level `scenario:`
- Portfolio documents: `crml_portfolio: "1.0"` with top-level `portfolio:`

## License

MIT License — see [LICENSE](LICENSE).

