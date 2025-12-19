# Engine Python API (`crml_engine`)

The engine package contains runtime entry points for executing CRML documents.

## Primary entry points

### Run a scenario

```python
from crml_engine.runtime import run_simulation

yaml_text = """
crml_scenario: "1.0"
meta:
  name: "example"
scenario:
  frequency:
    basis: per_organization_per_year
    model: poisson
    parameters: {lambda: 0.1}
  severity:
    model: lognormal
    parameters: {median: 22000, currency: USD, sigma: 1.0}
"""

result = run_simulation(yaml_text, n_runs=10000, seed=42)
assert result.success
print(result.metrics.eal)
```

### Run a portfolio

```python
from crml_engine.runtime import run_portfolio_simulation

res = run_portfolio_simulation("examples/portfolios/portfolio.yaml", source_kind="path", n_runs=10000, seed=42)
assert res.success
```

### Run a portfolio bundle

```python
from crml_engine.runtime import run_portfolio_bundle_simulation

res = run_portfolio_bundle_simulation("examples/portfolio_bundles/portfolio-bundle-documented.yaml", source_kind="path", n_runs=10000, seed=42)
assert res.success
```

## Results

The runtime returns a `SimulationResult` (engine-native) and can also produce an engine-agnostic `CRSimulationResult`.

See: [Engine capabilities: Results](Capabilities/Results.md)

## Engine-defined behavior

Model support and execution details are engine-defined.

See: [Capabilities](Capabilities/Supported-Models.md)
