# Simulation Result Schema (`crml_simulation_result: "1.0"`)

This page documents the CRML **Simulation Result** envelope shape and how to use it.

- JSON Schema: `crml_lang/src/crml_lang/schemas/crml-simulation-result-schema.json`
- Pydantic model: `crml_lang/src/crml_lang/models/simulation_result.py` (`CRSimulationResult`)

---

## What a simulation result is

A simulation result is an **engine-produced artifact** that reports:

- whether execution succeeded,
- engine identity and run metadata,
- standardized results (measures + artifacts).

It lives in `crml_lang` so that engines and UIs share a stable contract.

Most users should not hand-author result envelopes.

---

## Top-level structure

```yaml
crml_simulation_result: "1.0"
result: { ... }
```

---

## `result` fields

### Status fields

- `success` (bool)
- `errors` (list of strings)
- `warnings` (list of strings)

### Provenance fields

- `engine`: `{ name, version? }`
- `run`: optional run metadata (`runs`, `seed`, `runtime_ms`, `started_at`)
- `inputs`: optional captured input metadata (model name/version/description)
- `units`: optional unit metadata (currency + horizon)

### Result payload

`results` contains:

- `measures`: list of `{ id, value, unit?, parameters?, label? }`
- `artifacts`: list of artifacts (currently `histogram` and `samples`)

Artifact kinds:

- `histogram`: `{ kind: histogram, bin_edges: [...], counts: [...] }`
- `samples`: `{ kind: samples, values: [...], sample_count_total?, sample_count_returned? }`

---

## Minimal skeleton example

```yaml
crml_simulation_result: "1.0"
result:
  success: true
  errors: []
  warnings: []
  engine:
    name: crml_engine
    version: "..."
  run:
    runs: 10000
    seed: 123
  units:
    currency: { kind: currency, code: USD, symbol: "$" }
    horizon: annual
  results:
    measures:
      - id: eal
        value: 12345.67
    artifacts: []
```

---

## Validation / consumption

Consumers (web UI, reporting, BI) should validate against the schema and then treat unknown fields in `parameters`/`binning`/`sampling` as engine-defined.

Python:

```python
from crml_lang.models.simulation_result import CRSimulationResult
env = CRSimulationResult.model_validate(result_dict)
```
