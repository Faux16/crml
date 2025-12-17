# CRML Schemas

The CRML language is validated via JSON Schema (Draft 2020-12) plus additional semantic checks.

- `crml_lang` provides the **language** schemas and the validator.
- The `crml` CLI (from `crml_engine`) delegates document validation to `crml_lang`.

CRML is **not** a single schema: it is a set of document types, each with its own schema.

---

## Language schemas (`crml_lang`)

Canonical schema files live in:

```text
crml_lang/src/crml_lang/schemas/
```

Specifically:

- `crml-scenario-schema.json` (`crml_scenario: "1.0"`) — usage: [Schemas/Scenario](Schemas/Scenario)
- `crml-portfolio-schema.json` (`crml_portfolio: "1.0"`) — usage: [Schemas/Portfolio](Schemas/Portfolio)
- `crml-control-catalog-schema.json` (`crml_control_catalog: "1.0"`) — usage: [Schemas/Control-Catalog](Schemas/Control-Catalog)
- `crml-assessment-schema.json` (`crml_assessment: "1.0"`) — usage: [Schemas/Assessment](Schemas/Assessment)
- `crml-control-relationships-schema.json` (`crml_control_relationships: "1.0"`) — usage: [Schemas/Control-Relationships](Schemas/Control-Relationships)
- `crml-portfolio-bundle-schema.json` (`crml_portfolio_bundle: "1.0"`) — usage: [Schemas/Portfolio-Bundle](Schemas/Portfolio-Bundle)
- `crml-simulation-result-schema.json` (`crml_simulation_result: "1.0"`) — usage: [Schemas/Simulation-Result](Schemas/Simulation-Result)

In addition to JSON Schema validation, `crml_lang` performs semantic validation (examples):

- Cross-references exist and types match (e.g. portfolios reference valid scenarios).
- Consistency rules (e.g. portfolios that reference `assessments` must also reference `control_catalogs`).

---

## Engine-owned schemas (`crml_engine`)

Some documents are **execution-time configuration** and belong to an engine rather than to the language.

The reference engine includes an FX config schema:

```text
crml_engine/src/crml_engine/schemas/crml-fx-config-schema.json
```

Usage documentation: [Schemas/FX-Config](Schemas/FX-Config)

Engines MAY define additional runtime config documents; those are not part of the CRML language unless adopted into `crml_lang`.

---

## Programmatic validation

To validate programmatically:

```python
from crml_lang import validate

report = validate("doc.yaml", source_kind="path")
if not report.ok:
    raise SystemExit(report.render_text(source_label="doc.yaml"))
```

For exact field-by-field constraints, open the schema JSON files directly.
