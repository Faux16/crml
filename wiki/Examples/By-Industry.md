# Industry-Specific Examples

These examples illustrate an **industry benchmarking / baseline quantification** approach:

- Start from industry/regulatory data (threat landscape).
- Express a portable baseline as CRML **scenarios**.
- Build an organization-specific CRML **portfolio** that adds exposure (assets) and posture (controls).

This page stays **engine agnostic** and **UI agnostic**. Assume **CRML Studio** can store the documents, run validation, and trigger risk modelling in your chosen engine.

## Documents and workflow

Typical workflow:

1. Create one or more scenarios per threat class (breach, ransomware, outage, fraud).
2. Add industry tags, locale, and regulatory frameworks in `meta`.
3. Create a portfolio:
   - define assets/exposure
   - reference scenarios
   - optionally reference control catalogs and assessments
4. Validate portfolio (and referenced scenarios) in CRML Studio.
5. Run the portfolio through your engine.

Important modelling rule:

- Scenarios do not contain “asset counts”. Exposure is expressed in the portfolio (assets + scenario binding) or as an execution-time setting.

## Healthcare example: PHI breach baseline

Scenario (threat-centric):

```yaml
crml_scenario: "1.0"
meta:
  name: "healthcare-phi-breach"
  description: "Baseline PHI breach risk (illustrative numbers)."
  industries: [healthcare]
  regulatory_frameworks: [HIPAA, HITECH]
  locale:
    regions: [north-america]
scenario:
  frequency:
    basis: per_asset_unit_per_year
    model: poisson
    parameters:
      lambda: 0.04
  severity:
    model: lognormal
    parameters:
      median: "200 000"
      currency: USD
      sigma: 1.5
```

Portfolio (exposure + aggregation):

```yaml
crml_portfolio: "1.0"
meta:
  name: "healthcare-baseline"
portfolio:
  semantics:
    method: sum
    constraints:
      validate_scenarios: true
  assets:
    - name: phi_datastores
      cardinality: 250
      tags: [data, phi]
  scenarios:
    - id: phi_breach
      path: ./healthcare-phi-breach.yaml
      binding:
        applies_to_assets: [phi_datastores]
```

## Financial services example: PCI breach baseline

```yaml
crml_scenario: "1.0"
meta:
  name: "pci-breach"
  description: "Payment card data breach baseline (illustrative numbers)."
  industries: [financial-services]
  regulatory_frameworks: ["PCI DSS"]
  locale:
    regions: [north-america]
scenario:
  frequency:
    basis: per_organization_per_year
    model: poisson
    parameters:
      lambda: 0.03
  severity:
    model: lognormal
    parameters:
      median: "1 000 000"
      currency: USD
      sigma: 1.8
```

## SaaS / technology example: outage baseline

```yaml
crml_scenario: "1.0"
meta:
  name: "saas-outage"
  description: "Availability incident baseline (illustrative numbers)."
  industries: [technology]
  locale:
    regions: [north-america]
scenario:
  frequency:
    basis: per_organization_per_year
    model: poisson
    parameters:
      lambda: 3.0
  severity:
    model: lognormal
    parameters:
      median: "270 000"
      currency: USD
      sigma: 1.2
```

## Making the baselines organization-specific

In a portfolio (not in the scenario), you typically adjust:

- Exposure: asset cardinalities and scenario bindings.
- Posture: reference control catalogs + assessments.
- Aggregation: how scenarios combine (`sum`, `max`, `mixture`, `choose_one`).

## What is possible (today)

- You can build an industry-tagged library of scenarios and reuse it across portfolios.
- You can enforce consistency by validating portfolios and referenced documents.
- You can keep controls as portable documents (catalogs/assessments) and reference them from portfolios.

## Limitations / assumptions

- Parameter choices (rates, medians, sigmas) come from your sources and judgement; CRML does not provide industry statistics.
- Frequency/severity model identifiers are engine-defined; ensure your engine supports the model IDs you use.
- How exposure scales “per asset unit” depends on the runtime/engine; document your engine’s interpretation.
