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

Bundle a portfolio (inline referenced scenarios/packs into a self-contained artifact):

```python
from crml_lang import bundle_portfolio

report = bundle_portfolio("examples/portfolios/portfolio.yaml", source_kind="path")
print(report.ok)

bundle = report.bundle
assert bundle is not None
```

Bundle from in-memory models (no filesystem access required):

```python
from crml_lang import CRPortfolio, CRScenario, bundle_portfolio

portfolio = CRPortfolio.load_from_yaml("examples/portfolios/portfolio.yaml")
scenario = CRScenario.load_from_yaml("examples/scenarios/data-breach-simple.yaml")

report = bundle_portfolio(
	portfolio,
	source_kind="model",
	scenarios={"s1": scenario},
)
print(report.ok)
```

Plan a portfolio (deterministic engine pipeline step):

```python
from crml_engine.pipeline import plan_portfolio

plan = plan_portfolio("examples/portfolios/portfolio.yaml", source_kind="path")
print(plan.ok)
```
