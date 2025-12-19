# CLI (`crml_engine`)

The reference CLI is provided by the `crml-engine` package.

Install:

```bash
pip install crml-engine
```

Help:

```bash
crml --help
```

## Commands

### `crml validate <file>`

Validates a CRML document (schema + semantic checks) via `crml_lang`.

```bash
crml validate examples/scenarios/phishing.yaml
```

### `crml simulate <file>`

Runs a Monte Carlo simulation using the reference engine.

Supported inputs:

- `crml_scenario: "1.0"`
- `crml_portfolio: "1.0"`
- `crml_portfolio_bundle: "1.0"`

Examples:

```bash
# Scenario
crml simulate examples/scenarios/phishing.yaml --runs 10000

# Portfolio
crml simulate examples/portfolios/portfolio.yaml --runs 10000

# JSON output
crml simulate examples/scenarios/phishing.yaml --runs 20000 --format json > result.json
```

Options:

- `-n, --runs`: number of runs (default: 10000)
- `-f, --format`: `text` or `json`
- `--fx-config`: path to an FX config YAML document

Important:

- `--seed` is currently accepted by the CLI but is not wired through to the simulation wrapper yet. Do not rely on it for reproducibility.

### `crml explain <file>`

Renders a human-readable explanation of a CRML document.

```bash
crml explain examples/scenarios/phishing.yaml
```

## Exit codes

- `0`: success
- `1`: validation failure, simulation failure, or parse error
