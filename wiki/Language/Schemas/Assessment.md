# Assessment Schema (`crml_assessment: "1.0"`)

This page documents the CRML **Assessment** document shape and how to use it.

- JSON Schema: `crml_lang/src/crml_lang/schemas/crml-assessment-schema.json`
- Pydantic model: `crml_lang/src/crml_lang/models/assessment_model.py` (`CRAssessment`)

---

## What an assessment is

An assessment is an organization/tool-produced **control posture** dataset.

Per control, an assessment entry MUST provide exactly one of:

- **Quantitative posture fields**: `implementation_effectiveness` and/or `coverage` and/or `reliability`
- **SCF Capability Maturity Model (CMM)**: `scf_cmm_level` (0..5)

Entries MUST NOT mix both styles in the same control.

Assessments can be referenced from a portfolio. When a portfolio references assessments, it should also reference the corresponding control catalogs.

---

## Top-level structure

```yaml
crml_assessment: "1.0"
meta: { ... }
assessment:
  framework: "..."
  assessed_at: "..."  # optional
  assessments: [ ... ]
```

---

## Minimal example

```yaml
crml_assessment: "1.0"
meta:
  name: "Example assessment"
assessment:
  framework: "Org"
  assessed_at: "2025-12-17T10:15:30Z"
  assessments:
    - id: "org:iam.mfa"
      scf_cmm_level: 3 # Well-Defined
```

See also: `examples/control_assessments/control-assessment.yaml`.

---

## Assessment catalog fields

- `assessment.id` (optional): identifier for the assessment dataset
- `assessment.framework` (required): framework label (for humans/tools)
- `assessment.assessed_at` (optional): ISO 8601 timestamp
- `assessment.assessments` (required): list of per-control entries

---

## Per-control assessment entry

Each entry supports:

- `id` (required): canonical control id
- Either quantitative posture fields:
  - `implementation_effectiveness` (optional, 0..1)
  - `coverage` (optional): `{ value: 0..1, basis: <string> }`
  - `reliability` (optional, 0..1)

- Or SCF maturity:
  - `scf_cmm_level` (optional, 0..5):
  - 0 – Not Performed
  - 1 – Performed Informally
  - 2 – Planned & Tracked
  - 3 – Well-Defined
  - 4 – Quantitatively Controlled
  - 5 – Continuously Improving
- `question` (optional): prompt text for questionnaires
- `description` (optional): extra context (avoid copyrighted standard text)
- `notes` (optional)
- `ref` (optional): structured locator metadata (tools/UI)

---

## Using assessments in portfolios

A portfolio references assessments by path:

```yaml
portfolio:
  control_catalogs:
    - ../control_catalogs/control-catalog.yaml
  assessments:
    - ../control_assessments/control-assessment.yaml
```

Semantic rule:

- If `portfolio.assessments` is provided, `portfolio.control_catalogs` must also be provided.

---

## Validation

Python:

```python
from crml_lang import validate_assessment
report = validate_assessment("examples/control_assessments/control-assessment.yaml", source_kind="path")
assert report.ok
```
