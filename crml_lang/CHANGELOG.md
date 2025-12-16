# crml-lang Changelog

This changelog covers the `crml-lang` package (language/spec).

## 1.1.0

### Added
- CRML 1.1 Pydantic models
- Bundled CRML JSON Schema (`crml-schema.json`)
- Structured validator (`ValidationReport`, `ValidationMessage`)
- YAML load/dump helpers (`CRModel` + module-level helpers)

### Notes
- The CRML schema version is declared in CRML documents via `crml: "1.1"`.
