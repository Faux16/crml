# crml-engine Changelog

This changelog covers the `crml-engine` package (reference runtime/CLI).

## 1.2.0 - 2025-12-21

### Fixed
- Python 3.9 compatibility: Replaced union operator syntax (`|`) with `Union` type annotations
- Fixed `TypeError` in `frequency.py`, `engine.py`, and `fx_model.py` for Python 3.9 support

### Changed
- Updated dependency: `crml-lang>=1.2.0`
- Synced version with crml-lang package

## 1.2.0 (Initial)

### Added
- `crml` CLI (`validate`, `simulate`, `explain`)
- Monte Carlo simulation runtime
- FX configuration support for multi-currency normalization/output
- Control effectiveness application during simulation (for Poisson frequency)
- Per-asset frequency/severity models (multiple assets within one scenario file)

### Notes
- `crml-engine` depends on `crml-lang` for parsing and validation.
