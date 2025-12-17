# FX Config Schema (`crml_fx_config: "1.0"`) (engine-owned)

This page documents the reference engine’s **FX config** document.

- JSON Schema: `crml_engine/src/crml_engine/schemas/crml-fx-config-schema.json`
- Loader/model: `crml_engine/src/crml_engine/models/fx_model.py`

This document is **engine-owned** (runtime configuration), not part of the core CRML language.

---

## What an FX config is

An FX config defines:

- the base currency used for internal normalization,
- the output currency used for reporting,
- conversion rates.

It is used by the reference engine to convert monetary severity inputs/outputs.

---

## Top-level structure

```yaml
crml_fx_config: "1.0"
base_currency: USD
output_currency: USD
rates: { USD: 1.0, EUR: 1.08 }
as_of: "2025-01-15"  # optional
```

The schema allows additional engine-defined keys (`additionalProperties: true`).

---

## Minimal example

See: `examples/fx_configs/fx-config.yaml`

---

## Using FX config with the CLI

Typical usage:

- Provide the file to the engine at runtime with `--fx-config`.

Example:

- `crml simulate examples/portfolios/portfolio.yaml --fx-config examples/fx_configs/fx-config.yaml`

(Exact CLI subcommand/flags depend on the installed CLI version; this repository’s examples follow the reference engine.)

---

## Validation behavior

The reference engine:

- validates the file against its JSON Schema (Draft 2020-12),
- merges provided rates with defaults,
- warns and falls back to defaults if the file cannot be loaded.

If you need strict behavior (fail hard), implement that policy in your tooling/CI wrapper.
