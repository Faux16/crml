# Changelog

All notable changes to CRML will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2025-12-15

### Added
- **Control Effectiveness Modeling** - Major new feature for quantifying security control impact
  - New `controls` block in CRML schema with layers and dependencies
  - Support for effectiveness, coverage, and reliability parameters
  - Defense-in-depth calculations with multiplicative risk reduction
  - Control dependency and correlation modeling
  - ROI calculations for security investments
  - Comprehensive validation and error handling
  - New module `crml.controls` with core logic (360 lines)
  - 19 comprehensive test cases (100% pass rate)
  - Full documentation in `docs/controls-guide.md` (500+ lines)
  - Example model: `spec/examples/ransomware-with-controls.yaml`
  - Web UI integration with beautiful control effectiveness card

### Changed
- Updated `docs/writing-crml.md` with controls section
- Enhanced README.md with control effectiveness examples
- Web platform now displays baseline vs effective lambda comparison
- Improved simulation results with risk reduction metrics

### Fixed
- Fixed Python spawn command in web API (python → python3 for macOS)

### Documentation
- Added comprehensive control effectiveness guide
- Updated writing guide with control examples
- Added control type reference and best practices
- Included calibration guidance from vendor data and historical incidents

## [1.1.0] - 2024-XX-XX

### Added
- Median-based parameterization for lognormal distributions
- Multi-currency support with automatic conversion
- Auto-calibration from raw loss data
- JSON Schema validation
- CRML CLI tool
- Web playground for interactive modeling

### Changed
- Migrated from log-space `mu` to intuitive `median` parameter
- Enhanced documentation and examples

## [1.0.0] - 2024-XX-XX

### Added
- Initial release of CRML specification
- Basic frequency and severity modeling
- Poisson and lognormal distributions
- YAML-based model definition
- Python validator

---

## Version History

- **1.2.0** - Control Effectiveness Modeling
- **1.1.0** - Median parameterization, multi-currency, auto-calibration
- **1.0.0** - Initial release
