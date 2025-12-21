# Tool integration

This guide covers common integration surfaces.

---

## JSON output (CLI)

```bash
crml simulate model.yaml --runs 20000 --format json > result.json
```

---

## Python integration

- Language-level validation/loading: [Language Python API](../Language/Python-API.md)
- Runtime execution: [Engine Python API](../Engine/Python-API.md)

---

## Bundles for portability

If you need to run an engine without filesystem dependencies, use a `crml_portfolio_bundle`.

See:

- [Language/Schemas/Portfolio-Bundle](../Language/Schemas/Portfolio-Bundle.md)
- [Engine capabilities: Portfolio execution](../Engine/Capabilities/Portfolio-Execution.md)
