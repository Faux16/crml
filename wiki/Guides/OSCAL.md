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

- **convert OSCAL Catalogs** (JSON/YAML) into redistributable **CRML control catalogs** (minimal, metadata-only) for use in CRML scenarios, mappings, and portfolios, and
- (optionally) **publish CRML assessment outputs into OSCAL Assessment Results-style structures** using a documented convention (see below).

Important: CRML’s shipped OSCAL tooling today is **catalog-centric**. It converts **OSCAL catalogs → CRML** (control catalogs and assessment templates). It does **not** ingest OSCAL Assessment Results as a first-class quantitative input format.

In practice, teams often position them like this:

- **OSCAL** is well-suited as an interchange format for **compliance artifacts and organizational posture**: what controls exist, how they’re implemented, what was assessed, and what evidence supports the assessment.
- **CRML** acts as the bridge from posture to the **threat landscape** for risk modeling: it can reference and normalize threat/control catalogs and mappings (e.g., ATT&CK/CAPEC/internal catalogs) into modelable scenarios, then quantify outcomes.

The key idea:

- Use OSCAL for **interchange and auditability**.
- Use CRML for **quantification and computation**.

CRML’s quantitative outputs can be preserved in OSCAL using:

- `risk.characterizations` (preferred for likelihood/impact-like concepts), and
- `props` (for structured extensions, units, currencies, scale definitions, and tool-specific metadata).

## What CRML supports today (OSCAL)

CRML currently supports these OSCAL-related conversions:

- **OSCAL Catalog → CRML Control Catalog (minimal, metadata-only)**
  - Python: `CRControlCatalog.fromOscal(path)`
  - CLI: `crml-lang oscal import-catalog ...`
- **OSCAL Catalog → CRML Assessment template** (no posture values exist in catalogs)
  - Python: `CRAssessment.fromOscal(path)`
  - CLI: `crml-lang oscal import-assessment-template ...`

Endpoint-driven imports (built-in + user-extended) are supported via `crml-lang oscal list-endpoints` and `--endpoint`.

## Practical limitation: framework catalogs, licensing, and identifiers

In the real world, OSCAL representations of major control frameworks are often:

- published only on official standards bodies’ websites,
- sometimes behind paywalls or licensing terms, and
- may contain copyrighted material.

CRML documentation and examples in this repository therefore **SHOULD NOT** embed or redistribute copyrighted framework text.

For quantitative risk modeling, the *human-readable control description text* is usually not the critical input anyway. What matters most for modeling workflows is:

- stable control identifiers,
- a stable framework/catalog identifier, and
- the **relationships and mappings** (control-to-control, control-to-objective, control-to-threat/technique, coverage/overlap, inheritance).

### Practical limitation: OSCAL has no stable catalog identifier

OSCAL Catalog documents do not provide a single, standardized, globally stable identifier for “this is *the* catalog for framework X” that all tools can rely on.

In practice, implementers often fall back to unstable signals such as:

- the local file name,
- an access URL that can change over time,
- the metadata title string (human-facing), or
- publisher-specific UUIDs that are not standardized across catalogs or distributions.

For cross-framework work (e.g., CIS → internal org controls, or NIST → ISO mappings), a **stable global catalog identifier** is required. Without it, different tools can generate identical-looking control ids while referring to different catalog variants.

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

#### Stable framework/catalog identifier (required for mapping)

To do framework-to-framework mapping reliably, you must also be able to identify **which catalog/framework a namespace refers to**.

In CRML, stable mapping depends on using **stable control identifiers** (the `namespace:key` form) and keeping the `namespace` stable over time.

For standardized public frameworks, the recommended way to get stable namespaces is to import via the **shipped OSCAL endpoint list** (or an organization-provided extension of it). The endpoint provides a stable `catalog_id`, and CRML uses that value as the default control-id namespace (slugged if needed).

If you import directly from a local OSCAL file path (without an endpoint), the current implementation derives the namespace from the OSCAL catalog title (slugged). If that title changes, the namespace will change.

- The project ships a built-in OSCAL API endpoint list at `crml_lang/src/crml_lang/oscal/api-endpoints.yaml`.
- Each catalog endpoint includes a required `catalog_id` (stable dataset identifier) and a `url` (or `path`) for the OSCAL catalog.
- When you import via an endpoint, CRML uses `catalog_id` as the stable catalog identifier and (by default) as the control-id namespace.

This is intentional: only by using the shipped list can CRML implementations converge on the same stable identifiers.

Normative rules:

- For standardized public frameworks, the **stable catalog source URL** MUST be selected from the shipped endpoint list.
- The endpoint’s `catalog_id` MUST be treated as the stable dataset identifier for that framework.

If you need to work with a framework that is not in the shipped list, treat that as a catalog onboarding step: add it to your own endpoint file, distribute it alongside your CRML implementation(s) and open a pull request here for us to add it. (see “Endpoint config files” below).

### OSCAL → CRML control catalogs (practical ingestion)

If you have an OSCAL Catalog (JSON or YAML) for a framework, CRML can ingest it and generate a **redistributable, minimal** CRML control catalog.

The generated catalog intentionally keeps only:

- control identifiers (`id`),
- optional `oscal_uuid` (the OSCAL control UUID),
- short `title` (if present),
- optional `description` (derived from OSCAL control `parts[].prose`, if present; only include prose you have rights to distribute),
- a reference `url` (first OSCAL link, if present).

It still intentionally strips the structured OSCAL statements/parts tree, but it may copy human prose text into `description` for convenience. Be mindful of copyright and redistribution constraints.

Python API:

```python
from crml_lang import CRControlCatalog

catalog = CRControlCatalog.fromOscal("in-oscal-catalog.json", catalog_id="cisv8")

# Writes CRML YAML (not OSCAL YAML)
catalog.dump_to_yaml("out-crml-control-catalog.yaml")
```

CLI (single file):

```bash
crml-lang oscal import-catalog --path in-oscal-catalog.json --out out-crml-control-catalog.yaml
```

CLI (endpoint):

```bash
crml-lang oscal list-endpoints
crml-lang oscal import-catalog --endpoint bsi_gspp_2023 --out out-crml-control-catalog.yaml
```

When using `--endpoint`, CRML uses the endpoint’s `catalog_id` as the stable catalog identifier and as the default control-id namespace (so ids remain stable even if upstream OSCAL metadata like `title` changes).

### Endpoint config files (url/path)

OSCAL endpoints are configured via YAML with these top-level lists:

- `catalogs: [...]`
- `assets: [...]`
- `assessments: [...]`
- `mappings: [...]`

Each endpoint entry MUST specify **exactly one** of:

- `url: https://...` (remote OSCAL JSON/YAML)
- `path: ./relative/or/absolute.json` (local OSCAL JSON/YAML)

If `path` is relative, it is resolved relative to the config file location.

#### Optional locale metadata (regions/countries)

Endpoints may optionally declare locale metadata that will be copied into generated CRML artifacts under `meta.locale`.

The format matches CRML's existing convention used in scenarios/portfolios:

- `regions`: a list of lowercase-ish region tokens like `world`, `europe`, `north-america`
- `countries`: a list of ISO 3166-1 alpha-2 country codes like `DE`, `US`

Rules:

- You may set `regions` without `countries`.
- You MUST NOT set `countries` unless `regions` is also provided.

For backwards compatibility, endpoint files may also use singular `region`/`country` keys; they are normalized into `regions`/`countries`.

Example:

```yaml
catalogs:
  - catalog_id: my_catalog_v1
    description: My local OSCAL catalog
    path: ./oscal/catalog.json
    regions: [europe]
    countries: [DE]

assets: []
assessments: []
mappings: []
```

#### Built-in list + extending it in your environment

This project ships with a built-in (and intentionally expanding) endpoint list in `crml_lang/src/crml_lang/oscal/api-endpoints.yaml`.

You can extend or override endpoints in your environment by providing additional endpoint YAML files via the `CRML_OSCAL_ENDPOINTS_PATH` environment variable (path-separated). Endpoints are merged by `catalog_id` and later files override earlier ones.

This is the supported way to:

- add additional catalogs you have access to,
- pin an internal mirror URL, or
- introduce organization-specific frameworks.

### Importing catalogs into your environment (after cloning)

After cloning this repository, you can use the OSCAL endpoint tooling to populate your local CRML environment. The `examples/` folder provides convenient places to store generated artifacts.

Typical workflow:

1) List the shipped endpoints:

```bash
crml-lang oscal list-endpoints
```

2) Import a shipped catalog endpoint into a CRML control catalog YAML:

```bash
crml-lang oscal import-catalog --endpoint bsi_gspp_2023 --out examples/control_catalogs/bsi-gspp-control-catalog.yaml
crml-lang oscal import-catalog --endpoint bsi_gspp_2023 --out examples/control_catalogs/bsi-gspp-control-catalog.yaml
```

3) (Optional) Generate a CRML assessment template for the same framework (still sourced from the OSCAL catalog, so it has no measured posture values):

```bash
crml-lang oscal import-assessment-template --endpoint bsi_gspp_2023 --out examples/control_assessments/bsi-gspp-assessment-template.yaml
crml-lang oscal import-assessment-template --endpoint bsi_gspp_2023 --out examples/control_assessments/bsi-gspp-assessment-template.yaml
```

### Batch generation (catalogs only)

To generate CRML control catalogs for every catalog endpoint listed in a config file:

```bash
crml-lang oscal generate-catalogs --config path/to/api-endpoints.yaml --out-dir out/
```

This writes one `*-control-catalog.yaml` file per catalog endpoint into `out/`.

Notes:

- The endpoint's `catalog_id` becomes the `namespace` part in generated control ids like `cisv8:1.1` (unless `namespace` is explicitly set on the endpoint).
- The OSCAL control `id` becomes the `key` part.
- OSCAL control UUIDs are preserved in the CRML field `oscal_uuid` when present.

Normative rules:

- Each control catalog entry **MUST** have an `id` (`namespace:key`) that is stable over time.
- The `id` values inside a catalog **MUST** be unique (no duplicates).
- Mapping work **MUST** be performed against these identifiers (not titles, not prose descriptions).

Practical guidance:


- If you build cross-framework mappings (e.g., CISv8 → Org), it is usually simplest to include a complete catalog for the source framework so every `source_id` in the mapping has a corresponding catalog entry.

## Field mapping: OSCAL Catalog → CRML (implemented)

CRML's shipped OSCAL support today is **catalog-centric**. It supports importing an OSCAL Catalog (JSON/YAML) into:

- a CRML Control Catalog skeleton (`CRControlCatalog.fromOscal(...)` / `crml-lang oscal import-catalog`), and
- a CRML Assessment template (`CRAssessment.fromOscal(...)` / `crml-lang oscal import-assessment-template`).

These conversions intentionally keep only a minimal, redistributable subset of fields.

### Namespace and identifiers

CRML uses `namespace:key` identifiers as the canonical join key across catalogs, assessments, scenarios, and mappings.

Implemented rules:

- **Key**: the OSCAL control `id` becomes the CRML `key`.
- **Namespace**:
  - If importing via `--endpoint`, the namespace defaults to the endpoint's `catalog_id` (slugged if needed), unless the endpoint provides an explicit `namespace` override.
  - If importing via `--path`, the namespace defaults to a slug of the OSCAL catalog title.

### Control catalog fields (OSCAL Catalog → CRML Control Catalog)

| OSCAL source | CRML target | Notes |
|---|---|---|
| `catalog.metadata.title` (preferred) or `catalog.title` | `catalog.framework` | Human label only. |
| `catalog.controls[].id` (including nested groups/sub-controls) | `catalog.controls[].id` | Transformed into `namespace:key`. |
| `catalog.controls[].uuid` | `catalog.controls[].oscal_uuid` | Preserved as interoperability metadata. |
| `catalog.controls[].title` | `catalog.controls[].title` | Optional. |
| `catalog.controls[].links[0].href` | `catalog.controls[].url` | Optional; first link only. |

### Assessment template fields (OSCAL Catalog → CRML Assessment)

OSCAL catalogs do not include organization-specific posture values. The import therefore produces a template with a default SCF CMM level.

| OSCAL source | CRML target | Notes |
|---|---|---|
| `catalog.metadata.title` (preferred) or `catalog.title` | `assessment.framework` | Human label only. |
| `catalog.controls[].id` | `assessment.assessments[].id` | Transformed into `namespace:key`. |
| `catalog.controls[].uuid` | `assessment.assessments[].oscal_uuid` | Preserved as interoperability metadata. |
| *(no OSCAL equivalent)* | `assessment.assessments[].scf_cmm_level` | Defaulted (0 unless configured by the importer). |

## CRML → OSCAL Assessment Results (not implemented)

This repository currently does **not** implement exporting CRML results into OSCAL Assessment Results (`finding`/`risk`) objects.

The earlier "CRML → OSCAL" mapping tables (findings/risks/characterizations/`urn:crml` props) describe a **proposed convention** only.

When an original framework author/publisher provides an OSCAL representation, exporters/importers **SHOULD** treat the framework’s published identifier as canonical:

- Prefer the framework’s **human-readable identifier** (the control ID that humans cite, e.g., `AC-2`) as the primary mapping key.
- If OSCAL uses UUIDs internally, the UUID **SHOULD** be preserved alongside the human-readable identifier.
  In CRML, store that UUID in `oscal_uuid` on the control catalog entry (and optionally on assessment entries when assessments are shared without catalogs).

When no canonical OSCAL representation exists (or cannot be redistributed), CRML workflows **SHOULD** still operate by:

- minting stable IDs in an explicit namespace (e.g., `org:`, `vendor:`, or a URN scheme), and
- keeping catalogs minimal: identifiers + relationship structure + any non-copyrightable metadata needed for mapping.

### Minimal catalogs and licensed enrichment

CRML examples and reference catalogs are intentionally **minimal models**: they focus on identifiers and relationship structure, and avoid embedding copyrighted framework prose.

Organizations that have the appropriate rights **MAY** enrich these minimal catalogs locally by attaching the full, licensed control text and metadata sourced from the standards bodies themselves — either via:

- official OSCAL catalogs published by the framework owner, or
- licensed CRML control catalogs (if a standards body publishes CRML-native representations).

This keeps the public CRML ecosystem redistributable while still enabling full-fidelity internal catalogs where licensing permits.

## Publishing CRML assessment outputs into OSCAL (normative convention)

CRML is a better **native output format** for assessment tools that want to support quantified risk, because CRML standardizes the fields needed for risk math (distributions, time bases, currencies, and other numeric semantics).

OSCAL Assessment Results is excellent for interoperability and traceability, but it does not normatively define quantitative risk math (many values are open strings). As a result:

- **CRML → OSCAL** is possible (by writing CRML’s standardized values into OSCAL `risk.characterizations` and `props` using a clear convention), and
- **OSCAL → CRML** (for assessments/results) is not generally possible in a safe, non-lossy way, because the quantitative semantics are not standardized in OSCAL and are often tool-specific strings.

This section defines the normative convention for mapping CRML concepts to OSCAL Assessment Results-style `finding` and `risk` objects.

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
- CRML results can be represented in OSCAL by:
  - using `risk.characterizations` for likelihood/impact-like summaries,
  - using `props` for precise numeric values, units, currencies, and scale definitions.
