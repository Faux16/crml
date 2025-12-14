# CRML v1.1.0 - Multi-Currency & Median Parameterization 🌍

**Release Date:** December 2025

This release introduces significant improvements to currency handling and parameter specification, making CRML models more intuitive and maintainable.

## 🎯 Key Features

### 1. Median-Based Lognormal Parameterization

CRML 1.1 introduces human-readable `median` parameters for lognormal distributions, replacing the obscure log-space `mu` parameter:

**Before (CRML 1.0):**
```yaml
severity:
  model: lognormal
  parameters:
    mu: 11.51  # What does this mean?
    sigma: 1.2
```

**After (CRML 1.1):**
```yaml
severity:
  model: lognormal
  parameters:
    median: "100 000"  # $100K - directly from industry reports!
    currency: USD
    sigma: 1.2
```

The `mu` parameter is still supported for backward compatibility, but `median` is recommended.

### 2. ISO 80000-1 Number Format Support

Large numbers can use space-separated thousands for improved readability:

```yaml
# Both formats are valid:
median: 100000       # Standard numeric
median: "100 000"    # ISO 80000-1 format (spaces as thousands separators)
median: "1 000 000"  # One million, easier to read
```

This applies to large monetary values (`median`, `scale`) but NOT to mathematical factors (`mu`, `sigma`, `lambda`, `shape`).

### 3. Explicit Currency Declarations

All monetary parameters can now declare their currency explicitly:

```yaml
severity:
  model: lognormal
  parameters:
    median: "175 000"
    currency: EUR  # Explicit currency code
    sigma: 1.8
```

### 4. External FX Configuration

Currency conversion can now be handled via external FX configuration files.

**FX Config File (fx-config.yaml):**
```yaml
base_currency: USD
output_currency: EUR  # Display results in Euros
as_of: "2025-01-15"
rates:
  EUR: 1.08
  GBP: 1.26
  JPY: 0.0066
```

**Usage:**
```bash
crml simulate model.yaml --fx-config fx-config.yaml
```

Benefits:
- **Clean models** - Risk models focus on risk, not FX rates
- **Single source of truth** - Update rates in one place
- **Reproducibility** - FX rates are explicit and versioned

### 4. Multi-Currency Risk Models

Model risks across multiple jurisdictions with automatic currency normalization:

```yaml
# Example: GDPR (EUR) + CCPA (USD) compliance risk
severity:
  model: mixture
  components:
    - lognormal:
        weight: 0.27
        median: "175 000"
        currency: EUR  # GDPR fines
        sigma: 1.8
    - lognormal:
        weight: 0.73
        median: "250 000"
        currency: USD  # CCPA fines
        sigma: 1.5
```

## 🔧 CLI Changes

### New `--fx-config` Option

```bash
# New (CRML 1.1)
crml simulate model.yaml --fx-config fx-config-eur.yaml
```

### Updated Output

Results now show both currency code and symbol:

```
Currency: EUR (€)
EAL (Expected Annual Loss):  €27,100,000.00
```

## 📁 New Files

- `spec/examples/fx-config.yaml` - Default USD FX configuration
- `spec/examples/fx-config-eur.yaml` - Example EUR output configuration
- `spec/examples/multi-currency-example.yaml` - GDPR/CCPA compliance example

## ⚠️ Breaking Changes

None!

## 🔄 Migration Guide

### From CRML 1.0 to 1.1

1. **Update version number:**
   ```yaml
   crml: "1.1"  # Was "1.0"
   ```

2. **Replace `mu` with `median` (recommended):**
   ```yaml
   # Calculate: median = e^mu
   # Example: mu=11.51 → median ≈ "100 000"
   median: "100 000"
   currency: USD
   ```

3. **Create `fx-config.yaml` file:**
    If you have risks accross regions

## 📚 Documentation

- **Specification:** [spec/crml-1.1.md](spec/crml-1.1.md)
- **CLI Commands:** [docs/cli/cli-commands.md](docs/cli/cli-commands.md)
- **Writing CRML:** [docs/writing-crml.md](docs/writing-crml.md)

## 🙏 Acknowledgments

Thanks to @Xentraxx who provided feedback through the GitHub issues:
- Issue #2: Median-Based Lognormal Parameterization
- Issue #3: Explicit Currency Declaration and FX Context
and implemented the design proposals.
---

**Full Changelog:** [v1.0.0...v1.1.0](https://github.com/Faux16/crml/compare/v1.0.0...v1.1.0)
