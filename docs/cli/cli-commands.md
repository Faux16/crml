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

## `crml simulate`

Run a Monte Carlo simulation based on the CRML model.

```bash
crml simulate model.yaml -n 30000
```

Options:

- `-n, --runs` (int): number of Monte Carlo runs (default: 10000)
- `-s, --seed` (int): random seed for reproducibility
- `-f, --format` (text|json): output format (default: text)
- `--fx-config` (path): path to FX configuration file for currency conversion

### Currency Handling

Models should specify currency on monetary values:

```yaml
severity:
  model: lognormal
  parameters:
    median: "100 000"
    currency: EUR
    sigma: 1.2
```

To convert currencies and control output display, use an FX config file:

```bash
crml simulate model.yaml --fx-config fx-config.yaml
```

Example `fx-config.yaml`:

```yaml
base_currency: USD
output_currency: EUR  # Display results in Euros
as_of: "2025-01-15"
rates:
  EUR: 1.08
  GBP: 1.26
  JPY: 0.0066
```

Output example:

```text
==================================================
CRML Simulation Results
==================================================
Model: data-breach-simple
Runs: 10,000
Runtime: 45.23 ms
Currency: EUR (€)

==================================================
Risk Metrics
==================================================
EAL (Expected Annual Loss):  €27,100,000.00
VaR 95%:                      €39,700,000.00
VaR 99%:                      €44,300,000.00
VaR 99.9%:                    €68,400,000.00
==================================================
```

---

## `crml run` (legacy)

Alias for `crml simulate` with text output.

```bash
crml run model.yaml --runs 30000
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
