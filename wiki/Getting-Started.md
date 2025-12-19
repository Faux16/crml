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
crml validate examples/scenarios/scenario-phishing.yaml
```

---

## 3) Simulate a scenario

```bash
crml simulate examples/scenarios/scenario-phishing.yaml --runs 20000
```

For JSON output:

```bash
crml simulate examples/scenarios/scenario-phishing.yaml --runs 20000 --format json > result.json
```

---

## 4) Run a portfolio (exposure + multiple scenarios)

Portfolios bind scenarios to assets and scale per-asset frequency basis.

```bash
crml validate examples/portfolios/portfolio.yaml
crml simulate examples/portfolios/portfolio.yaml --runs 20000
```

Read the portable rules for exposure scaling here:

- [CRML Specification (Overview)](Reference/CRML-Specification.md)

---

## 5) Use multi-currency (FX config)

The reference engine supports an FX config document for output currency conversion.

See: [Multi-Currency Support](Multi-Currency-Support.md)
