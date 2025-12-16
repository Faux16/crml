# Language Python API (crml_lang)

Use `crml_lang` when you want to **load, validate, or transform** CRML documents.

## Load / dump YAML

```python
from crml_lang import CRModel

model = CRModel.load_from_yaml("model.yaml")
text = model.dump_to_yaml_str()
```

Load from a YAML string:

```python
from crml_lang import CRModel

yaml_str = """
crml: \"1.1\"
meta: {name: demo}
model:
  frequency: {model: poisson, parameters: {lambda: 0.1}}
  severity: {model: lognormal, parameters: {median: \"10 000\", currency: USD, sigma: 1.2}}
"""

model = CRModel.load_from_yaml_str(yaml_str)
```

## Validate

```python
from crml_lang import validate

report = validate("model.yaml", source_kind="path")
print(report.ok)
print(report.render_text(source_label="model.yaml"))
```

Notes:
- Validation is **structured** (errors/warnings/messages) and does not print by itself.
- The validator checks the CRML JSON Schema and additional semantic rules.
