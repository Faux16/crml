# Assessment Schema (`crml_assessment: "1.0"`)

This page documents the CRML **Assessment** document shape and how to use it.

- JSON Schema: `crml_lang/src/crml_lang/schemas/crml-assessment-schema.json`
- Legacy schema filename (backwards compatibility): `crml_lang/src/crml_lang/schemas/crml-control-assessment-schema.json`
- Pydantic model: `crml_lang/src/crml_lang/models/assessment_model.py` (`CRAssessmentSchema`)

---

## What an assessment is

An assessment is an organization/tool-produced **control posture** dataset:

- which controls exist,
- how effective they are (`implementation_effectiveness`),
- how broadly they are deployed (`coverage`),
- how reliable they are (`reliability`).

Assessments can be referenced from a portfolio. When a portfolio references assessments, it should also reference the corresponding control catalogs.

---

## Top-level structure

```yaml
crml_assessment: "1.0"  # also accepts crml_control_assessment for backwards compatibility
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
  name: "Example control assessment"
assessment:
  framework: "Org"
  assessed_at: "2025-12-17T10:15:30Z"
  assessments:
    - id: "org:iam.mfa"
      implementation_effectiveness: 0.7
      reliability: 0.99
      affects: frequency
      coverage:
        value: 0.9
        basis: employees
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
- `implementation_effectiveness` (optional, 0..1)
- `coverage` (optional): `{ value: 0..1, basis: <string> }`
- `reliability` (optional, 0..1)
- `affects` (optional): `frequency | severity | both` (default `frequency`)
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
    - ../control_cataloges/control-catalog.yaml
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
