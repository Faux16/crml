# crml-engine Changelog

This changelog covers the `crml-engine` package (reference runtime/CLI).

## 1.1.0

### Added
- `crml` CLI (`validate`, `simulate`, `explain`)
- Monte Carlo simulation runtime
- FX configuration support for multi-currency normalization/output
- Control effectiveness application during simulation (for Poisson frequency)
- Per-asset frequency/severity models (multiple assets within one scenario file)

### Notes
- `crml-engine` depends on `crml-lang` for parsing and validation.
