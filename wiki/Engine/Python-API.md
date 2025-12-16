# Engine Python API (crml_engine)

Use `crml_engine` when you want to **execute** CRML documents.

## Run a simulation

```python
from crml_engine.runtime import run_simulation

result = run_simulation("examples/scenarios/data-breach-simple.yaml", n_runs=10000, seed=123)
print(result.success)
print(result.metrics)
```

## Multi-currency output

```python
from crml_engine.runtime import run_simulation
from crml_engine.models.fx_model import load_fx_config

fx = load_fx_config("examples/fx_configs/fx-config.yaml")
result = run_simulation("examples/scenarios/multi-currency-example.yaml", n_runs=10000, fx_config=fx)
```

If you prefer the lower-level entrypoint, use:

```python
from crml_engine.simulation.engine import run_monte_carlo
```
