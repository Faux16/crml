# Example: FAIR-style Baseline Model

This page shows a FAIR-inspired “single scenario baseline” expressed using the current CRML document structure.

## Risk management approach

Use this approach when you want a transparent baseline that can support:

- initial quantification (“how big is this category of loss?”)
- sensitivity testing (“what if frequency halves?”)
- comparison over time (“before vs after a control program”) when combined with portfolios/controls

## Documents involved (engine/UI agnostic)

- A **Scenario** (`crml_scenario: "1.0"`) that encodes baseline frequency + severity.
- A **Portfolio** (`crml_portfolio: "1.0"`) that selects scenarios and defines aggregation semantics.

In CRML Studio, you typically create the scenario first, then build a portfolio that references it.

## Example scenario

```yaml
crml_scenario: "1.0"
meta:
  name: "fair-baseline"
  version: "2025.1"
  description: "FAIR-inspired baseline: Poisson frequency + lognormal severity."
scenario:
  frequency:
    basis: per_organization_per_year
    model: poisson
    parameters:
      lambda: 0.4
  severity:
    model: lognormal
    parameters:
      median: "60 000"
      currency: USD
      sigma: 1.0
```

## Example portfolio (single-scenario)

```yaml
crml_portfolio: "1.0"
meta:
  name: "fair-baseline-portfolio"
portfolio:
  semantics:
    method: sum
    constraints:
      validate_scenarios: true
  scenarios:
    - id: baseline
      path: ./fair-baseline.yaml
```

## Mapping to FAIR concepts (practical guidance)

Different teams map FAIR differently. A common, practical mapping is:

- Threat Event Frequency (TEF) → `frequency` (e.g., Poisson `lambda`)
- Loss Magnitude (LM) → `severity` (e.g., lognormal median + sigma)

If you explicitly model “vulnerability” as a probability term in FAIR, you typically encode that either:

- inside `lambda` (baseline × vulnerability factor), or
- via controls in a portfolio/runtime that reduces baseline likelihood.

## What is possible (today)

- You can keep the baseline scenario portable and reuse it across portfolios.
- You can attach currency to monetary severity inputs.
- You can later add a portfolio-level control posture (catalogs + assessments) to support “before/after” analysis.

## Limitations / assumptions

- CRML does not force a particular FAIR decomposition (TEF/VF/LM); that’s a modelling choice.
- Distribution/model identifiers are engine-defined; your engine must support the chosen `model` names.
- Parameter estimation (data sources, calibration, priors) is not standardized by CRML; document your sources.
