# Full Examples

This page points to the repo’s concrete example **documents** and explains how to use them for common risk-management workflows.

Everything here is **engine agnostic** and **UI agnostic**: CRML defines the document contracts, while engines decide which model IDs and runtime features they support.
Assume **CRML Studio** can be used to manage the documents, run validation, and trigger simulations/risk modelling through your configured engine.

## Example documents in this repository

### Scenarios (threat-centric)

- [examples/scenarios/fair-baseline.yaml](../../examples/scenarios/fair-baseline.yaml) (FAIR-inspired baseline)
- [examples/scenarios/data-breach-simple.yaml](../../examples/scenarios/data-breach-simple.yaml) (simple breach baseline)
- [examples/scenarios/ransomware-scenario.yaml](../../examples/scenarios/ransomware-scenario.yaml) (ransomware baseline)
- [examples/scenarios/ransomware-with-controls.yaml](../../examples/scenarios/ransomware-with-controls.yaml) (control-relevant threat)
- [examples/scenarios/multi-currency-example.yaml](../../examples/scenarios/multi-currency-example.yaml) (currency-tagged inputs)
- [examples/scenarios/qber-simplified.yaml](../../examples/scenarios/qber-simplified.yaml) (QBER-inspired structure)

### Portfolios (organization view)

- [examples/portfolios/portfolio.yaml](../../examples/portfolios/portfolio.yaml) (scenario aggregation, assets/exposure, control packs)

### Control catalogs and assessments

- [examples/control_cataloges/control-catalog.yaml](../../examples/control_cataloges/control-catalog.yaml)
- [examples/control_assessments/control-assessment.yaml](../../examples/control_assessments/control-assessment.yaml) (Assessment pack)

### FX config (execution-time)

- [examples/fx_configs/fx-config.yaml](../../examples/fx_configs/fx-config.yaml)
- [examples/fx_configs/fx-config-eur.yaml](../../examples/fx_configs/fx-config-eur.yaml)

## Practical workflows (how teams typically use these)

### Baseline quantification

1. Start with a baseline scenario (e.g., FAIR-style).
2. Create a one-scenario portfolio that references it.
3. Validate and run.
4. Capture assumptions and data sources in the scenario `meta`.

### Portfolio aggregation (enterprise view)

1. Create multiple scenarios for distinct threat classes.
2. Build a portfolio with explicit aggregation semantics.
3. Add assets/exposure and bind scenarios to the relevant assets if applicable.

### Control/posture driven analysis

1. Maintain canonical control IDs in a control catalog.
2. Track organization evidence in an assessment catalog.
3. Reference both from the portfolio.
4. Ensure each scenario declares which controls are relevant (scenario controls).

### Multi-currency reporting

1. Tag severity inputs with their currency.
2. Provide an external FX config at execution time.

## Limitations and portability notes

- Scenario/portfolio schemas are strict; avoid adding engine-specific keys into the CRML documents unless your tooling explicitly supports that.
- Model identifiers are engine-defined; not every engine will support `mixture` or hierarchical frequency models.
- “Pipelines” (MCMC, diagnostics, exports) are deliberately outside the CRML core documents; treat them as engine/tool configuration.