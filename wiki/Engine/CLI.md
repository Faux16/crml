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

Validates a CRML document (schema + semantic checks). This delegates to the `crml_lang` validator.

```bash
crml validate examples/scenarios/phishing.yaml
```

If you have the language tooling installed separately, you can also call the validator directly:

```bash
crml-lang validate examples/scenarios/phishing.yaml
```

### `crml simulate <file>`

Runs a Monte Carlo simulation using the reference engine.

Supported inputs:

- `crml_portfolio_bundle: "1.0"`

Important:

- Raw scenarios (`crml_scenario`) and portfolios (`crml_portfolio`) are **not** executable by the reference runtime.
	Create a `crml_portfolio_bundle` first (e.g. via `crml bundle-portfolio`).

Examples:

```bash
# Portfolio bundle (executable)
crml simulate examples/portfolio_bundles/portfolio-bundle-documented.yaml --runs 10000

# JSON output
crml simulate examples/portfolio_bundles/portfolio-bundle-documented.yaml --runs 20000 --format json > result.json
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
