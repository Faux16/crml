# Validation

CRML validation is split into two layers:

- **Schema validation**: ensures the document shape matches CRML 1.1 JSON Schema.
- **Semantic validation**: catches common modeling issues that are valid JSON/YAML, but unlikely to be intended.

## CLI vs library

- The `crml` CLI is provided by `crml_engine`.
- The validator itself lives in `crml_lang`.

If you only need validation in a pipeline, you can install `crml-lang` and call the validator from Python.

## Example

```python
from crml_lang import validate

report = validate("examples/scenarios/data-breach-simple.yaml", source_kind="path")
if not report.ok:
    raise SystemExit(report.render_text(source_label="examples/scenarios/data-breach-simple.yaml"))
```

## Numeric fields (wire vs in-memory)

Some numeric fields allow a **human-friendly wire format** in YAML, e.g.:

```yaml
median: "500 000"
```

During parsing/validation those values are interpreted as numbers.
