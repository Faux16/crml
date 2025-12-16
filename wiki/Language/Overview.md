# Language (crml_lang)

CRML (Cyber Risk Modeling Language) is a *document format* for describing cyber risk models.

The `crml_lang` Python package is the **language/spec implementation**:

- Pydantic models for CRML documents
- The CRML JSON Schema
- A structured validator that reports errors and warnings
- YAML load/dump helpers

If you want to *run simulations*, install and use the **engine** package instead: `crml_engine`.

## Versions: schema vs packages

- The **schema version** is declared in the model file as `crml: "1.1"`.
- The **Python package versions** (`crml-lang`, `crml-engine`) follow their own release cadence.

A CRML file declaring `crml: "1.1"` is a **CRML 1.1 document**, regardless of which engine executes it.
