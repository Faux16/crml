# CRML Schemas

The CRML language is validated via JSON Schema (as emitted by the `crml_lang` Pydantic models) plus additional semantic checks.

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

- `crml-scenario-schema.json` (`crml_scenario: "1.0"`) — usage: [Language/Schemas/Scenario](../Language/Schemas/Scenario.md)
- `crml-portfolio-schema.json` (`crml_portfolio: "1.0"`) — usage: [Language/Schemas/Portfolio](../Language/Schemas/Portfolio.md)
- `crml-control-catalog-schema.json` (`crml_control_catalog: "1.0"`) — usage: [Language/Schemas/Control-Catalog](../Language/Schemas/Control-Catalog.md)
- `crml-attack-catalog-schema.json` (`crml_attack_catalog: "1.0"`) — usage: [Language/Schemas/Attack-Catalog](../Language/Schemas/Attack-Catalog.md)
- `crml-attack-control-relationships-schema.json` (`crml_attack_control_relationships: "1.0"`) — usage: [Language/Schemas/Attack-Control-Relationships](../Language/Schemas/Attack-Control-Relationships.md)
- `crml-assessment-schema.json` (`crml_assessment: "1.0"`) — usage: [Language/Schemas/Assessment](../Language/Schemas/Assessment.md)
- `crml-control-relationships-schema.json` (`crml_control_relationships: "1.0"`) — usage: [Language/Schemas/Control-Relationships](../Language/Schemas/Control-Relationships.md)
- `crml-portfolio-bundle-schema.json` (`crml_portfolio_bundle: "1.0"`) — usage: [Language/Schemas/Portfolio-Bundle](../Language/Schemas/Portfolio-Bundle.md)
- `crml-simulation-result-schema.json` (`crml_simulation_result: "1.0"`) — usage: [Language/Schemas/Simulation-Result](../Language/Schemas/Simulation-Result.md)

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

Usage documentation: [Language/Schemas/FX-Config](../Language/Schemas/FX-Config.md)

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

---

## How schemas are generated

The JSON Schema files shipped in `crml_lang/src/crml_lang/schemas/` are generated from the Pydantic models in `crml_lang/src/crml_lang/models/`.

The generator script is:

```text
crml_lang/tools/generate_schemas.py
```

From the repo root, you can regenerate schemas with:

```bash
python crml_lang/tools/generate_schemas.py
```

Notes:

- If you change model fields/descriptions in `crml_lang`, regenerate schemas so docs and packaged schema JSON stay in sync.
