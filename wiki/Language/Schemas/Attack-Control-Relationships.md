# Attack→Control Relationships Schema (`crml_attack_control_relationships: "1.0"`)

This page documents the CRML **Attack→Control Relationships** document type.

- JSON Schema: `crml_lang/src/crml_lang/schemas/crml-attack-control-relationships-schema.json`
- Pydantic model: `crml_lang/src/crml_lang/models/attack_control_relationships_model.py` (`CRAttackControlRelationships`)

---

## What an attack→control relationships mapping is

An attack→control relationships mapping is a portable set of **grouped mappings** from an attack-pattern id (e.g., ATT&CK) to one or more control ids.

It is intended to support workflows like:

- a scenario (or dataset) references attack ids (e.g., `attck:T1059.003`),
- tools/engines translate these into candidate controls (`cisv8:...`, `iso27001:...`, `org:...`),
- the mapping provides provenance, relationship type, and optional strength/confidence.

CRML does **not** mandate attack→attack mappings (e.g., ATT&CK↔CAPEC). If you need those, that is an engine/tool responsibility.

---

## Top-level structure

```yaml
crml_attack_control_relationships: "1.0"
meta: { ... }
relationships:
  id: "..."              # optional
  relationships: [ ... ]
  metadata: { ... }       # optional
```

---

## Relationship mapping (grouped 1→N)

Each mapping entry groups all control targets for a single attack id:

- `attack` (required): attack-pattern id (recommended namespace: `attck`)
- `targets` (required): non-empty list of target entries

### Target entry

Each target entry has:

- `control` (required): canonical control id (`namespace:key`)
- `relationship_type` (required): one of
  - `mitigated_by`
  - `detectable_by`
  - `respondable_by`
- `strength` (optional, 0..1): tool/community-defined strength metric
- `confidence` (optional, 0..1): tool/community-defined confidence
- `description` (optional): free-form description (avoid copyrighted text)
- `references` (optional): provenance pointers
- `tags` (optional): tool tags

---

## Minimal example

```yaml
crml_attack_control_relationships: "1.0"
meta:
  name: "Example attack→control mappings"
relationships:
  id: "example-mapping"
  relationships:
    - attack: "attck:T1059.003"
      targets:
        - control: "cisv8:8.2"
          relationship_type: mitigated_by
          strength: 0.7
          confidence: 0.8
          references:
            - type: url
              url: https://example.com/mapping-notes
```

---

## Using attack→control relationships in portfolios

A portfolio may reference these mappings by path:

```yaml
portfolio:
  attack_control_relationships:
    - ../attack_control_relationships/attck-to-controls.yaml
```

---

## Validation

Python:

```python
from crml_lang import validate_attack_control_relationships
report = validate_attack_control_relationships("path/to/mapping.yaml", source_kind="path")
assert report.ok
```

````
