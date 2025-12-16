# Install the language package (crml_lang)

Install the CRML language/spec package:

```bash
pip install crml-lang
```

This gives you the CRML models + validator + YAML IO in Python.

## Verify

```bash
python -c "from crml_lang import CRModel, validate; print('crml_lang OK')"
```

## Want the CLI / simulator?

The `crml` CLI is provided by the engine package:

```bash
pip install crml-engine
```
