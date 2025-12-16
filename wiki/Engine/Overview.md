# Engine (crml_engine)

`crml_engine` is the **reference execution engine** for CRML documents.

It depends on `crml_lang` for parsing + validation, and provides:

- The `crml` CLI (`validate`, `simulate`, `explain`)
- A Python runtime for Monte Carlo simulation
- FX configuration support for multi-currency outputs
- Scenario correlation support (Gaussian copula over per-scenario frequency uniforms)

If you only need to *author / validate* CRML files, use `crml_lang` instead.
