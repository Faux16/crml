# crml-engine

Reference runtime/simulation engine for CRML.

Depends on `crml-lang` for the CRML models and validation.

## Install

```bash
pip install crml-engine
```

## CLI

Validate a scenario/portfolio document:

```bash
crml validate examples/scenarios/data-breach-simple.yaml
crml validate examples/portfolios/portfolio.yaml
```

Run a simulation:

```bash
crml simulate examples/scenarios/data-breach-simple.yaml --runs 10000
crml simulate examples/portfolios/portfolio.yaml --runs 10000
```

Notes:

- The `crml simulate` command auto-detects scenario vs portfolio inputs.
- Portfolio simulation uses `crml_lang.plan_portfolio` and applies portfolio semantics.

## Python

```python
from crml_engine.runtime import run_simulation

result = run_simulation("examples/scenarios/data-breach-simple.yaml", n_runs=10000)
print(result.metrics.eal)
```
