# Validation

CRML validation in this repo happens in two layers:

1. **Schema validation** (JSON Schema)
2. **Semantic validation** (cross-field and cross-document checks)

The canonical implementation lives in `crml_lang.validators`.

---

## Validate any document

Use `validate_document` to validate any supported CRML document type.

```python
from crml_lang import validate_document

report = validate_document("doc.yaml", source_kind="path")
if not report.ok:
    print(report.render_text(source_label="doc.yaml"))
```

Type detection is based on top-level discriminator keys (e.g., `crml_scenario`, `crml_portfolio`, ...).

---

## Portfolio semantic checks

Portfolio validation includes additional semantic checks such as:

- Ensuring referenced document types are consistent.
- Exposure/binding consistency checks (when cross-document inputs can be loaded).
- Constraints implied by the spec (e.g., portfolios that reference assessments must also reference control catalogs).

The portable semantics are documented in:

- [CRML Specification (Overview)](../Reference/CRML-Specification.md)

---

## CLI validation

The engine CLI delegates validation to `crml_lang`:

```bash
crml validate examples/scenarios/scenario-phishing.yaml
```

See: [Engine CLI](../Engine/CLI.md)
