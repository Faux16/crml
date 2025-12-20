# Getting Started

This guide expands on the [Quickstart](Quickstart.md) and shows a typical workflow across scenario and portfolio documents.

---

## 1) Install the engine (CLI)

```bash
pip install crml-engine
```

---

## 2) Validate a scenario

Pick an example scenario from the repo:

```bash
crml-lang validate examples/scenarios/scenario-phishing.yaml
```

---

## 3) Simulate (via a portfolio bundle)

The reference engine only executes **portfolio bundles** (`crml_portfolio_bundle`).

- A `crml_scenario` is not executable “in a vacuum” (it needs exposure/frequency context).
- A `crml_portfolio` is non-executable (it may reference other files); bundle it first.

```bash
crml simulate examples/portfolio_bundles/portfolio-bundle-documented.yaml --runs 20000
```

For JSON output:

```bash
crml simulate examples/portfolio_bundles/portfolio-bundle-documented.yaml --runs 20000 --format json > result.json
```

---

## 4) Bundle + run a portfolio (exposure + multiple scenarios)

Portfolios bind scenarios to assets and scale per-asset frequency basis.

```bash
crml-lang validate examples/portfolios/portfolio.yaml

# Create an executable bundle (self-contained artifact)
crml-lang bundle-portfolio examples/portfolios/portfolio.yaml portfolio-bundle.yaml

crml simulate portfolio-bundle.yaml --runs 20000
```

Read the portable rules for exposure scaling here:

- [CRML Specification (Overview)](Reference/CRML-Specification.md)

---

## 5) Use multi-currency (FX config)

The reference engine supports an FX config document for output currency conversion.

See: [Multi-Currency Support](Multi-Currency-Support.md)
