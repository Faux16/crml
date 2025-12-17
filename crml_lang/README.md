# crml-lang

Language/spec package for CRML.

- Pydantic models for CRML documents
- Bundled JSON Schema + structured validator
- YAML load/dump helpers (`CRScenario`, `CRPortfolio`)

## Quickstart

Validate a scenario document:

```python
from crml_lang import validate

report = validate("examples/scenarios/data-breach-simple.yaml", source_kind="path")
print(report.ok)
```

Load and work with typed models:

```python
from crml_lang import CRScenario

scenario = CRScenario.load_from_yaml("examples/scenarios/data-breach-simple.yaml")
print(scenario.meta.name)
```

Plan a portfolio (resolve scenarios, assets, controls, dependencies):

```python
from crml_lang import plan_portfolio

plan = plan_portfolio("examples/portfolios/portfolio.yaml", source_kind="path")
print(plan.ok)
```
