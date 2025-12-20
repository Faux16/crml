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

However, the catalog entries provide a **small, normalized contract** so engines and tools
can reliably interpret the meaning of an entry across different frameworks.

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

Key rules:

- `catalog.id` is the **namespace** for the catalog.
- Every attack entry `id` must begin with `<catalog.id>:`.
- Every attack entry must declare a normalized `kind` (enum) so engines can interpret it.
- `parent` and `phases` are **internal references** to other entries in the same catalog.

Exact fields are defined by the schema; open the schema JSON file for authoritative field-by-field constraints:

- `crml_lang/src/crml_lang/schemas/crml-attack-catalog-schema.json`

---

## Entry fields (`catalog.attacks[]`)

Required:

- `id`: namespaced identifier in canonical form `namespace:key`.
- `kind`: normalized entry kind enum.

Optional:

- `title`: short human-readable label.
- `url`: reference URL.
- `parent`: parent id in the same catalog (for hierarchical taxonomies).
- `phases`: list of phase-like ids in the same catalog (for step/tactic/phase association).
- `tags`: extra, non-semantic tags for UI grouping.

Notes:

- For ATT&CK, represent tactics as entries with `kind: tactic`, techniques with `kind: technique`, and sub-techniques with `kind: sub-technique`.
- For NIST CSF, represent Function/Category/Subcategory via `kind` and `parent`.
- For kill chains, phases are typically represented as entries with `kind: phase`.

---

## Example

```yaml
crml_attack_catalog: "1.0"
meta:
	name: "ATT&CK subset"
catalog:
	id: "attck"
	framework: "MITRE ATT&CK (Enterprise)"
	attacks:
		- id: "attck:TA0001"
			kind: "tactic"
			title: "Initial Access"
		- id: "attck:T1566"
			kind: "technique"
			title: "Phishing"
			phases: ["attck:TA0001"]
		- id: "attck:T1566.001"
			kind: "sub-technique"
			title: "Spearphishing Attachment"
			parent: "attck:T1566"
			phases: ["attck:TA0001"]
```

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
