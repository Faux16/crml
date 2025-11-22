# CRML CLI Commands

The `crml` command-line interface provides a thin wrapper around the Python
runtime.

---

## `crml validate`

Validate a CRML file against the JSON schema.

```bash
crml validate model.yaml
```

- Exits with code 0 on success
- Raises a JSON schema validation error on failure

---

## `crml run`

Run a Monte Carlo simulation based on the CRML model.

```bash
crml run model.yaml --runs 30000
```

Options:

- `--runs` (int): number of Monte Carlo runs (default: 20000)

Output example:

```text
=== CRML Simulation Results ===
EAL: 2.71e+07
VaR_95: 3.97e+07
VaR_99: 4.43e+07
VaR_999: 6.84e+07
```

---

## `crml explain`

Print a short human-readable summary of the model.

```bash
crml explain model.yaml
```

Example:

```text
CRML Model: financial-services-risk-model
Description: Unified enterprise cyber risk model.
Assets: 18000
Frequency model: gamma_poisson
Severity model: mixture
```

---

## Error handling

- Invalid YAML/JSON → loader error
- Schema mismatch → validation error
- Unknown model names → runtime `NotImplementedError`
