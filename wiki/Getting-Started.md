# Getting Started

This page is the canonical workflow for getting from “zero” to a working CRML simulation using the reference engine.

If you prefer a fully worked example set, jump straight to [Examples](Examples.md).

---

## Prerequisites

- Python 3.10+
- `pip`

---

## 1) Install the engine (CLI)

See: [Installation](Installation.md)

```bash
pip install crml-engine
```

Verify:

```bash
crml --help
```

---

## 2) Create (or pick) a scenario

Option A: start from a repo example:

```bash
crml-lang validate examples/scenarios/scenario-phishing.yaml
```

Option B: create your own `my-first-scenario.yaml`:

```yaml
crml_scenario: "1.0"
meta:
  name: "my-first-risk-model"
  description: "A simple phishing risk model"

scenario:
  frequency:
    basis: per_organization_per_year
    model: poisson
    parameters:
      lambda: 0.10

  severity:
    model: lognormal
    parameters:
      median: 22000
      currency: USD
      sigma: 1.0
```

Validate it:

```bash
crml-lang validate my-first-scenario.yaml
```

---

## 3) Create a portfolio, bundle it, and simulate

The reference engine only executes **portfolio bundles** (`crml_portfolio_bundle`).

- A `crml_scenario` is not executable “in a vacuum” (it needs exposure/frequency context).
- A `crml_portfolio` is non-executable (it may reference other files); bundle it first.

Create `my-first-portfolio.yaml`:

```yaml
crml_portfolio: "1.0"
meta:
  name: "my-first-portfolio"

portfolio:
  semantics:
    method: sum
    constraints:
      require_paths_exist: true
      validate_scenarios: true

  assets:
    - name: "org"
      cardinality: 1

  scenarios:
    - id: "s1"
      path: ./my-first-scenario.yaml
```

Bundle + simulate:

```bash
crml-lang validate my-first-portfolio.yaml
crml-lang bundle-portfolio my-first-portfolio.yaml my-first-portfolio-bundle.yaml

crml simulate my-first-portfolio-bundle.yaml --runs 10000
```

If you want a ready-made bundle from the repo:

```bash
crml simulate examples/portfolio_bundles/portfolio-bundle-documented.yaml --runs 20000
```

For JSON output:

```bash
crml simulate examples/portfolio_bundles/portfolio-bundle-documented.yaml --runs 20000 --format json > result.json
```

---

## 4) Optional: multi-currency (FX config)

The reference engine supports an FX config document for output currency conversion.

See: [Multi-Currency Support](Multi-Currency-Support.md)

---

## 4.5) Optional: generate control catalogs from OSCAL

This repo includes an OSCAL endpoints config at `crml_lang/src/crml_lang/oscal/api-endpoints.yaml`.

To generate CRML control catalogs for all catalog endpoints into the examples folder:

```bash
python -m crml_lang oscal export-catalogs \
  --config crml_lang/src/crml_lang/oscal/api-endpoints.yaml \
  --out-dir examples/control_catalogs \
  --sort-keys
```

Validate the generated files:

```bash
python -m crml_lang validate examples/control_catalogs/cisv8_1-control-catalog.yaml
python -m crml_lang validate examples/control_catalogs/bsi_gspp_2023-control-catalog.yaml
```

## 5) Optional: CRML Studio

If you want a visual interface, see: [CRML Studio Setup](Installation.md#crml-studio-setup)

---

## Next steps

- Semantics + portability rules: [CRML Specification (Overview)](Reference/CRML-Specification.md)
- Practical guidance: [Best Practices](Examples/Best-Practices.md)
- If you get stuck: [Troubleshooting](Reference/Troubleshooting.md)
