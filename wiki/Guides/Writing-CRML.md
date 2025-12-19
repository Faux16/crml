# Writing CRML models

This guide describes how to author CRML inputs in this repo’s **document-oriented** format.

Start here if you are new:

- [Quickstart](../Quickstart.md)
- [CRML Specification (Overview)](../Reference/CRML-Specification.md)

---

## The core split: scenario vs portfolio

- A **scenario** (`crml_scenario: "1.0"`) describes one risk model (frequency + severity + optional referenced controls).
- A **portfolio** (`crml_portfolio: "1.0"`) describes exposure (assets, cardinalities) and binds scenarios to assets.

Schemas:

- [Scenario](../Language/Schemas/Scenario.md)
- [Portfolio](../Language/Schemas/Portfolio.md)

---

## Minimal scenario

```yaml
crml_scenario: "1.0"
meta:
  name: "phishing"
scenario:
  frequency:
    basis: per_organization_per_year
    model: poisson
    parameters: {lambda: 0.1}
  severity:
    model: lognormal
    parameters: {median: 22000, currency: USD, sigma: 1.0}
```

---

## Exposure scaling

If you want “per asset unit per year” semantics, set:

- `scenario.frequency.basis: per_asset_unit_per_year`

Then bind the scenario to portfolio assets so exposure cardinality $E$ is defined.

The portable rules are specified here:

- [Exposure scaling and frequency basis](../Reference/CRML-Specification.md#exposure-scaling-and-frequency-basis-normative)

---

## Controls

Scenarios can reference controls by id; portfolios provide measured values for those ids.

See:

- [Control effectiveness](../Control-Effectiveness.md)
- [Engine capabilities: Controls](../Engine/Capabilities/Controls.md)

---

## Validate early

Use validation frequently while authoring:

```bash
crml validate my.yaml
```

See: [Validation](../Language/Validation.md)
