# Best Practices

These patterns help you build CRML models that are maintainable, auditable, and portable.

This guidance is **engine agnostic** and **UI agnostic**. Where workflows are mentioned, assume you can use **CRML Studio** to manage documents, run validation, and trigger risk modelling through your chosen engine.

## 1) Keep scenarios threat-centric and portable

In CRML, a **scenario** is a threat-centric definition (frequency + severity + optional scenario-scoped control references).

Best practice:

- Put the baseline threat model in a `crml_scenario: "1.0"` document.
- Do not embed exposure/inventory (asset counts) into the scenario.

Why:

- You can reuse the same scenario across organizations and portfolios.
- You can compare “threat landscape” separately from “organizational posture”.

## 2) Use portfolios for exposure, aggregation, and posture (we call this callibration)

Use a `crml_portfolio: "1.0"` document to:

- Define **assets/exposure** (inventory cardinalities and tags).
- Combine multiple scenarios with an explicit **semantics method** (`sum`, `max`, `mixture`, `choose_one`).
- Express **organizational control posture** (directly or via catalog + assessment packs).

In CRML Studio, this typically looks like:

1. Create/import scenario documents.
2. Create a portfolio representing your organisation and import the scenarios you want to simulate.
3. Validate the portfolio (and optionally validate referenced scenarios).
4. Run the simulation in your configured engine.

## 3) Treat engine-defined parts as explicit assumptions

CRML intentionally does not standardize all modelling internals.

- `scenario.frequency.model` and `scenario.severity.model` are **engine-defined identifiers**.
- Component structures (e.g., `severity.components`) may also be engine-defined.

Best practice:

- Write down the intended interpretation in `meta.description` and/or in your project documentation.
- Prefer a small set of model identifiers across your organization to keep models comparable.

## 4) Prefer human-auditable parameterization

For monetary severity inputs:

- Prefer `median` over `mu` when your engine supports it.
- Always include `currency` on monetary inputs.

For numeric readability:

- Use ISO-style digit grouping strings (e.g., `"100 000"`) if your tooling supports “numberish” parsing.

## 5) Model controls with a clean separation of concerns

Practical control modelling usually requires three layers:

- Scenario layer: which controls are relevant to the threat (scenario control references).
- Catalog layer: canonical control IDs and definitions (control catalogs).
- Assessment layer: organization-specific implementation evidence (assessments).

Best practice:

- Keep catalogs and assessments in their own documents.
- Reference those documents from a portfolio.
- Treat any “control effectiveness math” as engine-defined unless standardized in your spec.

## 6) Keep execution-time config out-of-band

Some concerns are intentionally execution-time configuration, not risk-model content:

- FX/rates for currency conversion.
- Random seeds, run counts, and runtime-specific options.

Best practice:

- Store these as separate config documents (or studio project settings), not in scenarios.

## 7) Document limitations explicitly

Every “real” model has limitations. Make them part of the example:

- Which parts are standardized by CRML vs chosen by the engine/tool.
- Which parameters are sourced from data vs expert judgement.
- What’s not modeled (e.g., second-order effects, tail dependencies, control degradation).
