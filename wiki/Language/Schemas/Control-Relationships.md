# Control Relationships Schema (`crml_control_relationships: "1.0"`)

This page documents the CRML **Control Relationships** document shape and how to use it.

- JSON Schema: `crml_lang/src/crml_lang/schemas/crml-control-relationships-schema.json`
- Pydantic model: `crml_lang/src/crml_lang/models/control_relationships_model.py` (`CRControlRelationships`)

---

## What a control relationships pack is

A control relationships pack is a portable set of **grouped control-to-control mappings** (1 to n) with quantitative overlap metadata.

It is intended to support workflows like:

- a scenario references control id `A` (threat-centric),
- a portfolio implements control id `B` (implementation-centric),
- the pack provides a mapping describing how each implemented `B` relates to `A` (e.g. overlap or equivalence), so engines/tools can reason about mitigation.

---

## Top-level structure

```yaml
crml_control_relationships: "1.0"
meta: { ... }
relationships:
  id: "..."           # optional
  relationships: [ ... ]
```

---

## Relationship mapping (grouped 1→N)

Each mapping entry groups all targets for a single source:

- `source` (required): canonical control id (often scenario/threat-centric)
- `targets` (required): non-empty list of target entries

### Target entry

Each target entry has:

- `target` (required): canonical control id (often portfolio/implementation-centric)
- `relationship_type` (optional): one of
  - `overlaps_with`, `mitigates`, `supports`, `equivalent_to`, `parent_of`, `child_of`, `backstops`
- `overlap` (required): quantitative overlap metadata
- `confidence` (optional, 0..1)
- `groupings` (optional): framework-agnostic taxonomy tags
- `description` (optional): free-form description (avoid copyrighted text)
- `references` (optional): provenance pointers

### `overlap`

`overlap.weight` is required and must be in `[0, 1]`.

Recommended semantics:

- `weight` is the fraction of the *source* control’s objective covered by the *target*.

Optional:

- `dimensions`: named sub-weights (tool/community-defined)
- `rationale`: explanation (avoid copyrighted text)

---

## Minimal example

```yaml
crml_control_relationships: "1.0"
meta:
  name: "Example mapping pack"
relationships:
  id: "org-mapping"
  relationships:
    - source: "cisv8:4.2"
      targets:
        - target: "org:edr"
          relationship_type: overlaps_with
          overlap:
            weight: 0.75
          confidence: 0.8
          references:
            - type: url
              url: https://example.com/mapping-notes
```

---

## Using control relationships in portfolios

A portfolio references packs by path:

```yaml
portfolio:
  control_relationships:
    - ../control_relationships/mapping-pack.yaml
```

Engines/tools may use these packs to resolve scenario controls to portfolio controls when ids are in different namespaces.

---

## Validation

## Excel (XLSX) authoring

If you prefer maintaining control mappings in Excel, CRML supports a strict XLSX workbook workflow and round-tripping to YAML:

- Guide: [Excel Controls & Mappings](../../Guides/Excel-Controls-and-Mappings.md)

Python:

```python
from crml_lang import validate_control_relationships
report = validate_control_relationships("path/to/pack.yaml", source_kind="path")
assert report.ok
```
