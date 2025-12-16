# CRML Schema

The CRML schema is implemented in JSON Schema (2020-12 draft) and is used by
the `crml_lang` validator. The `crml validate` CLI command (from `crml_engine`)
delegates validation to `crml_lang`.

At a high level, the schema enforces:

- presence of top-level keys: `crml`, `meta`, `model`
- types of primitive fields (strings, numbers, arrays, objects)
- minimal structure for `model.frequency` and `model.severity`

The canonical schema lives in:

```text
crml_lang/src/crml_lang/schemas/crml-schema.json
```

The portfolio schema (for linking multiple scenario files with validated aggregation semantics) lives in:

```text
crml_lang/src/crml_lang/schemas/crml-portfolio-schema.json
```

Example (truncated):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "CRML 1.1",
  "type": "object",
  "required": ["crml", "meta", "model"],
  "properties": {
    "crml": { "type": "string" },
    "meta": {
      "type": "object",
      "required": ["name"],
      "properties": {
        "name": { "type": "string" },
        "version": { "type": "string" },
        "description": { "type": "string" }
      }
    },
    "model": {
      "type": "object",
      "required": ["frequency", "severity"],
      "properties": {
        "assets": { "type": "object" },
        "frequency": { "type": "object" },
        "severity": { "type": "object" }
      }
    }
  }
}
```

To validate a model programmatically:

```python
from crml_lang import validate

report = validate("model.yaml", source_kind="path")
if not report.ok:
  raise SystemExit(report.render_text(source_label="model.yaml"))
```

For exact field-by-field constraints, open `crml-schema.json` directly.
