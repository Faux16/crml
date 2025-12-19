# Multi-Currency Support

CRML supports explicit currencies on monetary severity inputs and optional FX configuration for deterministic conversions and reporting.

This page documents the behavior of the **reference engine** (`crml_engine`) as implemented today.

- Overview and examples: [Quickstart](Quickstart)
- Full reference: [CRML Specification](Reference/CRML-Specification)
- CLI usage: [Quickstart](Quickstart)

## What you can express in CRML

Currency can be attached to severity inputs via `scenario.severity.parameters.currency`.

Example (lognormal median in EUR):

```yaml
crml_scenario: "1.0"
meta:
	name: "example"
scenario:
	frequency:
		basis: per_organization_per_year
		model: poisson
		parameters:
			lambda: 1
	severity:
		model: lognormal
		parameters:
			median: 100000
			currency: EUR
			sigma: 1.2
```

## How the reference engine handles currencies

At runtime, the engine uses an FX configuration (`fx_config`) with two roles:

- **Normalization**: severity inputs are converted into `fx_config.base_currency` before sampling.
- **Reporting**: after simulation, results are reported in `fx_config.output_currency`.

If you do not provide an FX config, the engine uses a default config (USD base/output + built-in default rates).

### What gets converted

The reference engine currently converts the following severity parameters:

- **Lognormal**
	- `median` is converted from `parameters.currency` into `base_currency`.
	- `mu` is adjusted by `ln(rate)` when a non-base currency is specified.
	- `single_losses` are converted into `base_currency` before calibration.
- **Gamma**
	- `scale` is converted from `parameters.currency` into `base_currency`.

### Reporting currency

After the simulation, if `base_currency != output_currency`, the engine converts the sampled annual losses from base to output.
The output currency appears in:

- `SimulationResult.metadata.currency_code` / `SimulationResult.metadata.currency`
- The engine-agnostic result document: `CRSimulationResult.result.units.currency`

### Notes / current limitations

- The engine’s default rates are authored with **USD as the base**.
	If you set `base_currency` to something else, you must also provide a `rates` table that is consistent with that base.
- The current severity **mixture** implementation is simplified and uses only the first component.

## FX config document

FX config is a separate YAML document type (not a CRML scenario/portfolio). It is identified by a top-level discriminator:

```yaml
crml_fx_config: "1.0"
base_currency: USD
output_currency: EUR
as_of: "2025-01-15"  # optional
rates:
	USD: 1.0
	EUR: 1.08
	GBP: 1.26
```

Rate semantics used by the reference engine:

- `rates[CCY]` is the value of **1 unit of `CCY` in `base_currency`**.
	For example, with `base_currency: USD`, `rates.EUR: 1.08` means 1 EUR = 1.08 USD.
- Conversion is performed as:

	```text
	amount_to = amount_from * rate_from / rate_to
	```

Examples you can start from:

- [examples/fx_configs/fx-config.yaml](../examples/fx_configs/fx-config.yaml)
- [examples/fx_configs/fx-config-eur.yaml](../examples/fx_configs/fx-config-eur.yaml)

## Using FX config

### CLI

Use `--fx-config` with `simulate`:

```bash
crml simulate examples/scenarios/multi-currency-example.yaml --fx-config examples/fx_configs/fx-config-eur.yaml
```

### Python API

You can pass FX config either as a dict or as an `FXConfig` instance:

```python
from crml_engine.runtime import run_simulation

fx_config = {
		"base_currency": "USD",
		"output_currency": "EUR",
		"rates": {"USD": 1.0, "EUR": 1.08},
}

result = run_simulation(yaml_content, n_runs=10000, seed=42, fx_config=fx_config)
```
