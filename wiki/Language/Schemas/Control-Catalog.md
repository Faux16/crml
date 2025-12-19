# Control Catalog Schema (`crml_control_catalog: "1.0"`)

This page documents the CRML **Control Catalog** document shape and how to use it.

- JSON Schema: `crml_lang/src/crml_lang/schemas/crml-control-catalog-schema.json`
- Pydantic model: `crml_lang/src/crml_lang/models/control_catalog_model.py` (`CRControlCatalog`)

---

## What a control catalog is

A control catalog is a **portable list of canonical control ids** with lightweight metadata.

It is designed for:

- tools to display and group controls,
- portfolios/assessments to share a consistent set of ids,
- avoiding any need to embed copyrighted standard text.

---

## Top-level structure

```yaml
crml_control_catalog: "1.0"
meta: { ... }
catalog:
  framework: "..."
  controls: [ ... ]
```

---

## Minimal example

```yaml
crml_control_catalog: "1.0"
meta:
  name: "Example control catalog"
catalog:
  id: "org"
  framework: "Org"
  controls:
    - id: "org:iam.mfa"
      title: "Multi-factor authentication"
      tags: ["iam"]
    - id: "org:edr"
      title: "Endpoint detection and response"
      tags: ["endpoint", "detection"]
```

See also: `examples/control_catalogs/control-catalog.yaml`.

---

## Catalog fields

- `catalog.id` (optional): organization/community identifier for the catalog
- `catalog.framework` (required): free-form label for humans/tools (e.g. `CIS v8`, `ISO27001:2022`, `Org`)
- `catalog.controls` (required): list of `ControlCatalogEntry`

---

## Control entry fields

Each entry is intentionally minimal:

- `id` (required): canonical id (`namespace:key`)
- `title` (optional): short human-readable label
- `url` (optional): pointer to reference material
- `tags` (optional): free-form tags
- `ref` (optional): structured locator metadata for tools
- `defense_in_depth_layers` (optional): list of layer tags with allowed values: `prevent`, `detect`, `respond`, `recover`

### `defense_in_depth_layers` (defense-in-depth)

Optional metadata to help tools and humans represent *defense-in-depth* in a portfolio/catalog.

This field allows multiple tags per control, but only from a fixed set of values.

Example:

```yaml
- id: "org:siem"
  defense_in_depth_layers: ["detect", "respond"]
```

### `ref` (structured locator)

`ref` is optional metadata for mapping/linking to an external standard. It is **not** the canonical reference mechanism; use `id`.

Current shape:

```yaml
ref:
  standard: "CIS"   # required
  control: "2"      # required
  requirement: "..."  # optional free-form requirement text (avoid copyrighted text)
```

Notes:

- `requirement` is optional free-form text. Only include requirement text you have rights to share.
- The standard/version/granularity should be encoded in the canonical `id`.

---

## Validation

## Excel (XLSX) authoring

If you prefer maintaining control definitions in Excel, CRML supports a strict XLSX workbook workflow and round-tripping to YAML:

- Guide: [Excel Controls & Mappings](../../Guides/Excel-Controls-and-Mappings.md)

Python:

```python
from crml_lang import validate_control_catalog
report = validate_control_catalog("examples/control_catalogs/control-catalog.yaml", source_kind="path")
assert report.ok
```
