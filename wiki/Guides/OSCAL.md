# OSCAL and CRML

CRML and OSCAL solve adjacent problems:

- **OSCAL (NIST Open Security Controls Assessment Language)** is a *standard interchange format* for controls, assessments, and assessment results.
- **CRML** is a *risk modeling language* aimed at **quantification** (distributions, simulation, calibration, currencies), and at making those assumptions reviewable and reproducible.

## Why OSCAL is not “built for quantification”

OSCAL’s assessment results model is intentionally designed to support:

- traceability (what control/objective/component an assessment result applies to),
- evidence linking (observations),
- lifecycle and workflow (status),
- interoperability across tools.

It is intentionally **not** designed to standardize quantitative risk math:

- Findings do **not** have native numeric fields for *severity, likelihood, impact*.
- Risk “characterizations” are **open strings**; OSCAL does not enforce units, scales, or calculations.

That’s why OSCAL by itself is not a quantitative risk modeling standard.

## How CRML relates to OSCAL

CRML can still interoperate with OSCAL because CRML can:

- **ingest OSCAL-like assessment artifacts** (findings/risks) as structured inputs to a portfolio and governance workflow, and
- **export CRML outcomes** into OSCAL Assessment Results structures so other governance/compliance tooling can consume them.

In practice, teams often position them like this:

- **OSCAL** is well-suited as an interchange format for **compliance artifacts and organizational posture**: what controls exist, how they’re implemented, what was assessed, and what evidence supports the assessment.
- **CRML** acts as the bridge from posture to the **threat landscape** for risk modeling: it can reference and normalize threat/control catalogs and mappings (e.g., ATT&CK/CAPEC/internal catalogs) into modelable scenarios, then quantify outcomes.

The key idea:

- Use OSCAL for **interchange and auditability**.
- Use CRML for **quantification and computation**.

CRML’s quantitative outputs can be preserved in OSCAL using:

- `risk.characterizations` (preferred for likelihood/impact-like concepts), and
- `props` (for structured extensions, units, currencies, scale definitions, and tool-specific metadata).

## Practical limitation: framework catalogs, licensing, and identifiers

In the real world, OSCAL representations of major control frameworks are often:

- published only on official standards bodies’ websites,
- sometimes behind paywalls or licensing terms, and
- may contain copyrighted material.

CRML documentation and examples in this repository therefore **SHOULD NOT** embed or redistribute copyrighted framework text.

For quantitative risk modeling, the *human-readable control description text* is usually not the critical input anyway. What matters most for modeling workflows is:

- stable control identifiers,
- and the **relationships and mappings** (control-to-control, control-to-objective, control-to-threat/technique, coverage/overlap, inheritance).

### Normative identifier rules

CRML does **not** try to ship or maintain a global registry of every control framework.
Instead, CRML’s rule is: **every control you reference must exist (by id) in at least one control catalog you include**.

In practice, catalogs look like the CISv8 example in this repo (note the `cisv8:` namespace):

```yaml
catalog:
  id: "cisv8"         # optional document grouping identifier (organization-owned)
  framework: "CIS v8"  # human label
  controls:
    - id: "cisv8:1.1"
    - id: "cisv8:1.2"
```

CRML’s canonical join key is the control entry `id` in the form `namespace:key`.

### OSCAL → CRML skeleton catalogs (practical ingestion)

If you have an OSCAL Catalog (JSON or YAML) for a framework, CRML can ingest it and generate a **redistributable skeleton** CRML control catalog.

The skeleton intentionally keeps only:

- control identifiers (`id`),
- optional `oscal_uuid` (the OSCAL control UUID),
- short `title` (if present),
- a reference `url` (first OSCAL link, if present).

It intentionally strips detailed statements/parts and any long copyrighted prose.

Python API:

```python
from crml_lang import CRControlCatalog

catalog = CRControlCatalog.fromOscal("in-oscal-catalog.json", catalog_id="cisv8")

# Writes CRML YAML (not OSCAL YAML)
catalog.dump_to_yaml("out-crml-control-catalog.yaml")
```

Notes:

- `--namespace` becomes the `namespace` part in generated control ids like `cisv8:1.1`.
- The OSCAL control `id` becomes the `key` part.
- OSCAL control UUIDs are preserved in the CRML field `oscal_uuid` when present.

Normative rules:

- Each control catalog entry **MUST** have an `id` (`namespace:key`) that is stable over time.
- The `id` values inside a catalog **MUST** be unique (no duplicates).
- Mapping work **MUST** be performed against these identifiers (not titles, not prose descriptions).

Practical guidance:


- If you build cross-framework mappings (e.g., CISv8 → Org), it is usually simplest to include a complete catalog for the source framework so every `source_id` in the mapping has a corresponding catalog entry.

When an original framework author/publisher provides an OSCAL representation, exporters/importers **SHOULD** treat the framework’s published identifier as canonical:

- Prefer the framework’s **human-readable identifier** (the control ID that humans cite, e.g., `AC-2`) as the primary mapping key.
- If OSCAL uses UUIDs internally, the UUID **SHOULD** be preserved alongside the human-readable identifier.
  In CRML, store that UUID in `oscal_uuid` on the control catalog entry (and optionally on assessment entries when assessments are shared without catalogs).

When no canonical OSCAL representation exists (or cannot be redistributed), CRML workflows **SHOULD** still operate by:

- minting stable IDs in an explicit namespace (e.g., `org:`, `vendor:`, or a URN scheme), and
- keeping catalogs minimal: identifiers + relationship structure + any non-copyrightable metadata needed for mapping.

### “Skeleton” catalogs and licensed enrichment

CRML examples and reference catalogs are intentionally **skeleton models**: they focus on identifiers and relationship structure, and avoid embedding copyrighted framework prose.

Organizations that have the appropriate rights **MAY** enrich these skeleton catalogs locally by attaching the full, licensed control text and metadata sourced from the standards bodies themselves — either via:

- official OSCAL catalogs published by the framework owner, or
- licensed CRML control catalogs (if a standards body publishes CRML-native representations).

This keeps the public CRML ecosystem redistributable while still enabling full-fidelity internal catalogs where licensing permits.

## Mapping rules (normative)

This section defines rules for mapping CRML concepts to OSCAL Assessment Results-style `finding` and `risk` objects.

### Conventions

- **UUID stability:** OSCAL requires stable `uuid` values. When CRML does not already have a UUID for an artifact, exporters **SHOULD** generate deterministic UUIDv5 values from stable CRML identifiers.
- **Namespace for CRML extensions:** Use `props[].ns = "urn:crml"` for CRML-specific values.
- **Name convention:** Use `props[].name` without a `crml:` prefix (because `ns` already carries the namespace).
- **Units and scales:** Any numeric value exported into OSCAL **MUST** include units in the same string, or accompany it with unit metadata in `props` (see below).

### 1) Finding object — fields and mapping

A `finding` documents what was observed during an assessment.

**OSCAL finding shape (summary)**

```yaml
finding:
  uuid: uuid
  title: string
  description: markup
  rationale: markup
  remark: string

  target:
    type: component | objective | control
    target-id: uuid
    status:
      state: satisfied | not-satisfied | partial | not-applicable
      reason: string

  related-observations:
    - observation-uuid

  related-risks:
    - risk-uuid

  origins:
    - actor:
        type: assessor | tool | party
        actor-uuid: uuid

  props:
    - name: string
      value: string
      ns: uri
      class: string

  links:
    - href: uri
      rel: string
      media-type: string
```

#### Field mapping rules

| OSCAL finding field | CRML source | Rule |
|---|---|---|
| `finding.uuid` | CRML stable ID (preferred) | **MUST** be stable across exports. If CRML has no UUID, **SHOULD** compute deterministic UUIDv5 from `(assessment_id, target_id, finding_kind)`.
| `finding.title` | Control/objective/component label | **SHOULD** be a short label. Example: `"Control assessment: org:iam.mfa"`.
| `finding.description` | CRML assessment notes / observed condition | **SHOULD** describe what was observed. Markup allowed.
| `finding.rationale` | CRML rationale for why it matters | **MAY** explain why this finding affects risk/compliance.
| `finding.remark` | Freeform | **MAY** hold additional context.
| `finding.target.type` | CRML reference kind | **MUST** be `control` when finding is about a control; `component` when about a system component; `objective` when about a requirement/objective.
| `finding.target.target-id` | Identifier of target | **MUST** be a UUID in OSCAL. If CRML uses non-UUID IDs (e.g., `org:iam.mfa`), **MUST** also store that original ID in `props` (see below).
| `finding.target.status.state` | CRML posture state | **MUST** map to one of: `satisfied`, `not-satisfied`, `partial`, `not-applicable`.
| `finding.target.status.reason` | CRML explanation | **SHOULD** capture “why” (e.g., missing evidence, not implemented).
| `finding.related-observations[]` | Evidence references | **MAY** link to evidence/telemetry observations if available.
| `finding.related-risks[]` | Derived risk UUIDs | **MAY** reference risks created/updated due to this finding.
| `finding.origins[].actor.type` | Producer | **MUST** be `tool` for CRML engine exports; **MAY** be `assessor` for human-entered findings.
| `finding.origins[].actor.actor-uuid` | Tool/assessor identity | **SHOULD** be stable for the same producer.
| `finding.links[]` | Traceability links | **SHOULD** link to CRML artifacts (scenario/portfolio path, run report URL, commit).

#### CRML extension props for findings

Because OSCAL findings have no native severity/likelihood/impact fields:

- Quantitative or categorical values attached to a finding **MUST** be represented using `props`.

Recommended CRML property names:

- `target.external_id` — original CRML target identifier if OSCAL `target-id` is a generated UUID
- `confidence` — e.g., `"0.7"` or `"high"`
- `severity` — if you need a single roll-up, use a string with scale info (e.g., `"high (org-scale-v1)"`)

### 2) Risk object — fields and mapping

A `risk` represents potential loss or harm, not an observation.

**OSCAL risk shape (summary)**

```yaml
risk:
  uuid: uuid
  title: string
  description: markup
  statement: markup

  status: open | investigating | mitigated | accepted | closed

  origins:
    - source:
        type: finding | observation | threat | vulnerability
        uuid-ref: uuid

  threat-ids:
    - string

  characterizations:
    - facet: likelihood | impact | confidence | exposure | severity
      value: string

  mitigation:
    uuid: uuid
    description: markup
    implementation:
      uuid: uuid
      description: markup

  props:
    - name: string
      value: string
      ns: uri
      class: string

  links:
    - href: uri
      rel: string
      media-type: string
```

#### Field mapping rules

| OSCAL risk field | CRML source | Rule |
|---|---|---|
| `risk.uuid` | CRML stable risk ID | **MUST** be stable across exports. If derived from a scenario, **SHOULD** be deterministic from `(scenario_id, portfolio_id, risk_kind)`.
| `risk.title` | CRML scenario/output label | **SHOULD** be a short label (e.g., `"Ransomware loss risk"`).
| `risk.description` | CRML narrative summary | **MAY** summarize key assumptions and scope.
| `risk.statement` | Formal risk statement | **SHOULD** follow “If X then Y resulting in Z”.
| `risk.status` | Workflow status | If CRML has no lifecycle state, **MUST** default to `open`.
| `risk.origins[].source.type` | Source type | **MUST** be one of `finding`, `observation`, `threat`, `vulnerability`. For CRML simulation results, **SHOULD** use `observation`. For posture-driven items, **SHOULD** use `finding`.
| `risk.origins[].source.uuid-ref` | Source UUID | **SHOULD** reference the upstream object (finding/observation) when known.
| `risk.threat-ids[]` | Threat catalog refs | **MAY** include external IDs like ATT&CK technique IDs.
| `risk.mitigation` | CRML mitigation/control strategy | **MAY** reference the mitigation plan; use `implementation` for what is actually in place.
| `risk.links[]` | Traceability | **SHOULD** link to CRML run outputs and model artifacts.

### 3) Risk characterizations (very important)

OSCAL does not define numeric scales.

Example:

```yaml
characterizations:
  - facet: likelihood
    value: high
  - facet: impact
    value: medium
```

Allowed facet values are open strings, but typical facets include:

- `likelihood`
- `impact`
- `severity`
- `confidence`
- `exposure`

#### Quantitative export rule

If CRML produces numeric likelihood/impact outputs, exporters **MUST NOT** pretend OSCAL defines math for those numbers.

Instead:

1) Prefer encoding numeric values as strings with units inside `risk.characterizations[]`.

Examples:

- `facet: likelihood`, `value: "0.15 / year"`
- `facet: impact`, `value: "USD 250000 (median)"`
- `facet: severity`, `value: "USD 1.2M (P95)"`

2) For machine-readability, also include structured values in `risk.props[]`.

Recommended property set:

- `likelihood.annual_rate` → `"0.15"`
- `impact.median.currency` → `"USD"`
- `impact.median.value` → `"250000"`
- `severity.p95.currency` → `"USD"`
- `severity.p95.value` → `"1200000"`
- `time_basis` → `"per_organization_per_year"`

This preserves CRML’s quantitative results while keeping OSCAL semantics honest.

#### Optional qualitative bucketing rule

If an organization requires `high/medium/low` buckets, exporters **MUST** also export the bucket definition as `props`, e.g.:

- `scale.likelihood` → `"org-scale-v1: low<0.05, medium<0.2, high>=0.2 (/year)"`

## Minimal example: CRML → OSCAL risk

```yaml
risk:
  uuid: 2ad9c1ee-6f05-5d2b-8a49-9d9a7c5aaf5f
  title: "Ransomware loss risk"
  statement: "If ransomware occurs, then operations are disrupted resulting in financial loss."
  status: open
  origins:
    - source:
        type: observation
        uuid-ref: 6d3aefc6-1e7a-5df0-9c70-4f8d0c54a6f3
  characterizations:
    - facet: likelihood
      value: "0.15 / year"
    - facet: impact
      value: "USD 250000 (median)"
    - facet: severity
      value: "USD 1200000 (P95)"
  props:
    - name: "likelihood.annual_rate"
      value: "0.15"
      ns: "urn:crml"
      class: "number"
    - name: "impact.median.currency"
      value: "USD"
      ns: "urn:crml"
      class: "string"
    - name: "impact.median.value"
      value: "250000"
      ns: "urn:crml"
      class: "number"
```

## Summary

- OSCAL is excellent for interoperable assessment result interchange and traceability.
- CRML is designed for quantified modeling and computation.
- CRML can export results into OSCAL by:
  - using `risk.characterizations` for likelihood/impact-like summaries,
  - using `props` for precise numeric values, units, currencies, and scale definitions.
