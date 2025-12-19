# Engine installation (`crml_engine`)

To run simulations, install the engine package:

```bash
pip install crml-engine
```

This installs the `crml` CLI.

Verify:

```bash
crml --help
```

Notes:

- The engine depends on `crml_lang` for document validation and schema models.
- If you are developing from source in this monorepo, prefer installing the sub-packages (`crml_lang/` and `crml_engine/`) rather than the repo root package.
