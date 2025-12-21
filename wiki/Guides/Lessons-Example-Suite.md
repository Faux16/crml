# Lessons: Example Suite (Controls + ATT&CK + CIS)

This guide is a **teaching progression** through a curated set of example CRML documents.

Goals:

- Show how a scenario becomes executable when referenced from a portfolio.
- Show **two** control workflows:
  1) **Direct org controls** (scenarios reference your internal `org:*` control ids)
  2) **Portable CIS controls** (scenarios reference `cisv8:*` ids; then map to internal controls)
- Demonstrate an explicit **ATT&CK → CIS** mapping artifact and how it relates to scenario authoring.

Non-goals (for now):

- Per-asset frequency scaling and `binding.applies_to_assets` are **documented** but kept **commented out** in these lessons so the runnable path stays consistent and beginner-friendly.
  - See the inline `OPTIONAL (advanced)` blocks in the lesson portfolios.

---

## Prerequisites

There are two supported ways to run these lessons.

### Option A: Installed CLI (recommended)

Install the reference engine (CLI):

```bash
pip install crml-engine
```

Useful commands:

```bash
crml validate <path-to-yaml>
crml simulate <path-to-portfolio-bundle.yaml> --runs 20000
```

Tip: use a smaller `--runs` (e.g. `2000`) while iterating.

### Option B: Repo checkout (no install)

If you are running directly from a git checkout (without installing packages), set `PYTHONPATH` so Python imports the `src/` packages instead of the top-level folders:

PowerShell:

```powershell
$env:PYTHONPATH = "$PWD\crml_lang\src;$PWD\crml_engine\src"
python -m crml_engine.cli validate <path-to-yaml>
python -m crml_engine.cli simulate <path-to-portfolio-bundle.yaml> --runs 20000
```

For the rest of this guide, if you are using Option B, replace:

- `crml ...` with `python -m crml_engine.cli ...`

---

## Lesson 1 — A minimal portfolio

**What you learn**

- A scenario is portable by itself.
- A portfolio makes one or more scenarios executable (and sets aggregation semantics).

**Files**

- Portfolio: [examples/portfolios/lesson-01-baseline-single-scenario.yaml](../../examples/portfolios/lesson-01-baseline-single-scenario.yaml)
- Scenario: [examples/scenarios/fair-baseline.yaml](../../examples/scenarios/fair-baseline.yaml)

**Run**

```bash
crml validate examples/portfolios/lesson-01-baseline-single-scenario.yaml
crml simulate examples/portfolio_bundles/lesson-01-baseline-single-scenario-bundle.yaml --runs 20000
```

---

## Lesson 2 — Direct mapping: scenario → org controls

**What you learn**

- The simplest executable control workflow:
  - scenario lists relevant controls (by internal id)
  - portfolio provides implementation/posture (via assessments and/or portfolio controls)

**Files**

- Scenario: [examples/scenarios/lesson-02-phishing-org-controls.yaml](../../examples/scenarios/lesson-02-phishing-org-controls.yaml)
- Portfolio: [examples/portfolios/lesson-02-direct-org-controls.yaml](../../examples/portfolios/lesson-02-direct-org-controls.yaml)
- Org control catalog: [examples/control_catalogs/lesson-org-control-catalog.yaml](../../examples/control_catalogs/lesson-org-control-catalog.yaml)
- Org assessment: [examples/control_assessments/lesson-org-control-assessment.yaml](../../examples/control_assessments/lesson-org-control-assessment.yaml)

**Run**

```bash
crml validate examples/portfolios/lesson-02-direct-org-controls.yaml
crml simulate examples/portfolio_bundles/lesson-02-direct-org-controls-bundle.yaml --runs 20000
```

---

## Lesson 3 — Scenario-scoped control factor vs org posture

**What you learn**

- `effectiveness_against_threat` belongs to the **scenario** (threat-specific assumption).
- Control posture belongs to the **portfolio** (org-specific implementation).
- The reference engine combines them multiplicatively in the portfolio planner.

This lesson is split into two runnable portfolios so you can diff results cleanly.

**Files**

- Scenario A: [examples/scenarios/lesson-02-phishing-org-controls.yaml](../../examples/scenarios/lesson-02-phishing-org-controls.yaml)
- Scenario B: [examples/scenarios/lesson-03-phishing-variant-org-controls.yaml](../../examples/scenarios/lesson-03-phishing-variant-org-controls.yaml)
- Portfolio runner A: [examples/portfolios/lesson-03a-org-controls-phishing.yaml](../../examples/portfolios/lesson-03a-org-controls-phishing.yaml)
- Portfolio runner B: [examples/portfolios/lesson-03b-org-controls-phishing-variant.yaml](../../examples/portfolios/lesson-03b-org-controls-phishing-variant.yaml)

**Run**

```bash
crml validate examples/portfolios/lesson-03a-org-controls-phishing.yaml
crml simulate examples/portfolio_bundles/lesson-03a-org-controls-phishing-bundle.yaml --runs 20000

crml validate examples/portfolios/lesson-03b-org-controls-phishing-variant.yaml
crml simulate examples/portfolio_bundles/lesson-03b-org-controls-phishing-variant-bundle.yaml --runs 20000
```

---

## Lesson 4 — Portable authoring: scenario → CIS controls (+ explicit ATT&CK → CIS mapping)

**What you learn**

- A scenario can be authored against **portable framework ids** (`cisv8:*`) instead of internal ids.
- You can attach `meta.attck` as metadata, then use an explicit mapping pack (ATT&CK → CIS) to propose relevant CIS controls.

**Files**

- Scenario: [examples/scenarios/lesson-04-phishing-attck-cis-controls.yaml](../../examples/scenarios/lesson-04-phishing-attck-cis-controls.yaml)
- ATT&CK catalog (subset): [examples/attack_catalogs/attck-catalog.yaml](../../examples/attack_catalogs/attck-catalog.yaml)
- ATT&CK → CIS mapping pack (lesson): [examples/attack_control_relationships/lesson-04-attck-to-cisv8-phishing.yaml](../../examples/attack_control_relationships/lesson-04-attck-to-cisv8-phishing.yaml)
- CIS v8 control catalog: [examples/control_catalogs/cisv8-control-catalog.yaml](../../examples/control_catalogs/cisv8-control-catalog.yaml)
- Portfolio (treat CIS as canonical controls): [examples/portfolios/lesson-04-cis-controls-scenario-portable.yaml](../../examples/portfolios/lesson-04-cis-controls-scenario-portable.yaml)

**Run**

```bash
crml validate examples/portfolios/lesson-04-cis-controls-scenario-portable.yaml
crml simulate examples/portfolio_bundles/lesson-04-cis-controls-scenario-portable-bundle.yaml --runs 20000
```

---

## Lesson 5 — Mapping layer: CIS → org controls (reusable across organizations)

**What you learn**

- How to represent a CIS→Org mapping as a `crml_control_relationships` pack.
- How that mapping is used by **tools** to translate portable scenarios into internal control programs.

Important note about the reference engine:

- The reference engine currently expects **scenario control ids** to match ids in portfolio inventory/assessment.
- It does **not** automatically apply control-to-control mapping packs at runtime.

So this lesson includes:

- A mapping pack (portable artifact for tools)
- A runnable portfolio that also includes a “tool output” section: CIS controls derived from org posture (so the scenario can run today)

**Files**

- CIS→Org mapping pack: [examples/control_relationships/lesson-05-cisv8-to-org-mapping.yaml](../../examples/control_relationships/lesson-05-cisv8-to-org-mapping.yaml)
- Portfolio: [examples/portfolios/lesson-05-cis-to-org-mapping-layer.yaml](../../examples/portfolios/lesson-05-cis-to-org-mapping-layer.yaml)

**Run**

```bash
crml validate examples/portfolios/lesson-05-cis-to-org-mapping-layer.yaml
crml simulate examples/portfolio_bundles/lesson-05-cis-to-org-mapping-layer-bundle.yaml --runs 20000
```

---

## Lesson 6 — Bundle format (exchange artifact)

**What you learn**

- How to package a portfolio + scenarios + catalogs + assessments + mappings into a single portable document.

**Files**

- Bundle: [examples/portfolio_bundles/lesson-06-bundle-direct-org-controls.yaml](../../examples/portfolio_bundles/lesson-06-bundle-direct-org-controls.yaml)
- Reference bundle (long-form): [examples/portfolio_bundles/portfolio-bundle-documented.yaml](../../examples/portfolio_bundles/portfolio-bundle-documented.yaml)

**Run**

```bash
crml validate examples/portfolio_bundles/lesson-06-bundle-direct-org-controls.yaml
crml simulate examples/portfolio_bundles/lesson-06-bundle-direct-org-controls.yaml --runs 20000
```

---

## Troubleshooting

- If `crml` is not found: either install `crml-engine` (Option A) or use `python -m crml_engine.cli` with `PYTHONPATH` (Option B).
- If validation complains about unknown control ids: ensure your portfolio references the right catalogs/assessments, and that scenario ids align with those.
