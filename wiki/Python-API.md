# Python API

While the CLI is convenient for ad-hoc runs, real integrations often use the
Python API directly.

---

## `crml.loader`

```python
from crml.loader import load_crml

model = load_crml("model.yaml")
```

- Accepts YAML or JSON.
- Returns a Python `dict`.

---

## `crml.validator`

```python
from crml.validator import validate_crml

validate_crml(model)
```

- Raises `jsonschema.ValidationError` if the model does not conform to
  `crml_schema.json`.

---

## `crml.runtime`

```python
from crml.runtime import run_model, explain_model

results = run_model(model, runs=20000)
print(results)

print(explain_model(model))
```

`run_model` returns a dictionary:

```python
{
  "EAL": 2.7136410e+07,
  "VaR_95": 3.9736940e+07,
  "VaR_99": 4.4349590e+07,
  "VaR_999": 6.8422817e+07
}
```

---

## `crml.frequency`, `crml.severity`, `crml.entropy`

You can also call the low-level functions directly:

```python
from crml.frequency import sample_gamma_poisson_frequency
from crml.severity import sample_mixture
from crml.entropy import entropy_from_counts
```

These are useful for:

- custom experimental models
- notebooks
- research papers
