# CRML Schema

The CRML schema is implemented in JSON Schema (2020-12 draft) and is used by
the `crml.validator` module and `crml validate` CLI command.

At a high level, the schema enforces:

- presence of top-level keys: `crml`, `meta`, `model`
- types of primitive fields (strings, numbers, arrays, objects)
- minimal structure for `model.frequency` and `model.severity`

The canonical schema lives in:

```text
crml/schema/crml_schema.json
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
from crml.loader import load_crml
from crml.validator import validate_crml

model = load_crml("model.yaml")
validate_crml(model)  # raises jsonschema.ValidationError on failure
```

For exact field-by-field constraints, open `crml_schema.json` directly.
