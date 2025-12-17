# Portfolio Bundle Schema (`crml_portfolio_bundle: "1.0"`)

This page documents the CRML **Portfolio Bundle** artifact shape and how to use it.

- JSON Schema: `crml_lang/src/crml_lang/schemas/crml-portfolio-bundle-schema.json`
- Pydantic model: `crml_lang/src/crml_lang/models/portfolio_bundle.py` (`CRPortfolioBundle`)

---

## What a portfolio bundle is

A portfolio bundle is a **language-produced artifact** that inlines a portfolio and all referenced documents into a single self-contained object.

Key properties:

- Intended as the contract between `crml_lang` and engines.
- Designed so engines do not need filesystem access (everything is inlined).

Most users should not hand-author bundles; they are produced by tooling (e.g., `crml_lang.bundle`).

---

## Top-level structure

```yaml
crml_portfolio_bundle: "1.0"
portfolio_bundle:
  portfolio: { ... }
  scenarios: [ ... ]
  control_catalogs: [ ... ]
  assessments: [ ... ]
  control_relationships: [ ... ]
  warnings: [ ... ]
  metadata: { ... }
```

---

## Key sections

### `portfolio_bundle.portfolio`

The full inlined portfolio document (`CRPortfolioSchema`).

### `portfolio_bundle.scenarios`

A list of inlined scenarios with portfolio ids:

- `id`: scenario id from the portfolio
- `weight`: optional
- `source_path`: traceability only
- `scenario`: the full inlined scenario document

### `control_catalogs`, `assessments`, `control_relationships`

Inlined documents corresponding to any packs referenced by the portfolio.

### `warnings`

Non-fatal bundling warnings; tools should surface these to users.

### `metadata`

Free-form traceability metadata; engines should not interpret it.

---

## Minimal skeleton example

```yaml
crml_portfolio_bundle: "1.0"
portfolio_bundle:
  portfolio: { crml_portfolio: "1.0", meta: {name: "..."}, portfolio: { ... } }
  scenarios:
    - id: phishing
      scenario: { crml_scenario: "1.0", meta: {name: "..."}, scenario: { ... } }
  control_catalogs: []
  assessments: []
  control_relationships: []
  warnings: []
  metadata: {}
```

---

## Validation

Python:

```python
from crml_lang.models.portfolio_bundle import CRPortfolioBundle
bundle = CRPortfolioBundle.model_validate(bundle_dict)
```
