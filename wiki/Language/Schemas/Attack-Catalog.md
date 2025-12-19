# Attack Catalog Schema (`crml_attack_catalog: "1.0"`)

This page documents the CRML **Attack Catalog** document shape and how to use it.

- JSON Schema: `crml_lang/src/crml_lang/schemas/crml-attack-catalog-schema.json`
- Pydantic model: `crml_lang/src/crml_lang/models/attack_catalog_model.py` (`CRAttackCatalog`)

---

## What an attack catalog is

An attack catalog is a **metadata pack** for attack-pattern identifiers.

Typical uses:

- Provide stable ids and human labels for UI/tooling
- Provide optional URLs/tags for navigation and grouping
- Serve as a reference set that scenarios/portfolios/tools can point at

Attack catalogs are intentionally **non-executable** and **engine-agnostic**.

---

## Top-level structure

```yaml
crml_attack_catalog: "1.0"
meta: { ... }
catalog: { ... }
```

---

## `catalog`

The catalog contains entries keyed by a stable identifier.

Exact fields are defined by the schema; open the schema JSON file for authoritative field-by-field constraints:

- `crml_lang/src/crml_lang/schemas/crml-attack-catalog-schema.json`

---

## Validation

CLI:

```bash
crml validate path/to/attack-catalog.yaml
```

Python:

```python
from crml_lang import validate_document

report = validate_document("path/to/attack-catalog.yaml", source_kind="path")
print(report.ok)
```
