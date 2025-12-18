# CRML System Architecture

CRML is organized into three layers:

- **Language/spec (`crml_lang`)**: schemas, models, validation, YAML IO
- **Runtime/engine (`crml_engine`)**: CLI + simulation runtime + portfolio execution + result serialization
- **Web UI (`web/`)**: CRML Studio (Next.js UI + API routes that call the CLI/runtime)

In addition to these layers, most real deployments also use **calibration tooling**:

- **Calibration tools (separate tool responsibility but might be part of an engine)**: ingest organization-specific evidence (e.g., incident logs) and write back calibrated CRML scenarios/portfolios.

For the detailed architecture, see:

- [Architecture-Language](Architecture-Language)
- [Architecture-Engine](Architecture-Engine)

## Document types

- Scenario documents: `crml_scenario: "1.0"` (top-level `scenario:`)
- Portfolio documents: `crml_portfolio: "1.0"` (top-level `portfolio:`; if `portfolio.assessments` is used, `portfolio.control_catalogs` must also be provided)
- Control catalog documents: `crml_control_catalog: "1.0"` (top-level `catalog:`)
- Attack catalog documents: `crml_attack_catalog: "1.0"` (top-level `catalog:`)
- Attack→control relationships documents: `crml_attack_control_relationships: "1.0"` (top-level `relationships:`; attack-pattern to control mappings)
- Assessment documents: `crml_assessment: "1.0"` (top-level `assessment:`)
- Control relationships documents: `crml_control_relationships: "1.0"` (top-level `relationships:`; control-to-control mappings with overlap metadata)
- FX config documents: `crml_fx_config: "1.0"` (top-level `base_currency`, `output_currency`, `rates`, optional `as_of`; engine-owned config document)
- Portfolio bundle artifacts: `crml_portfolio_bundle: "1.0"` (top-level `portfolio_bundle:`)
- Simulation result artifacts: `crml_simulation_result: "1.0"` (top-level `result:`)

See also:

- [Reference/CRML-Schema](../Reference/CRML-Schema.md) (where schemas live and how they’re generated)
- [Language/Schemas/Scenario](../Language/Schemas/Scenario.md) and [Language/Schemas/Portfolio](../Language/Schemas/Portfolio.md)

## Responsibility boundaries (why this split exists)

CRML intentionally splits responsibilities so tools can interoperate cleanly:

- `crml_lang` owns *document shape* (schemas), *validation*, and the *interchange contracts* used between tools/engines.
- `crml_engine` (and other engines) own *execution semantics* for engine-defined `model` strings and runtime configuration.

Attack-graph semantics and **attack→attack** mappings are explicitly an engine/tool responsibility:

- CRML mandates the ability to incorporate a baseline attack catalog (typically **MITRE ATT&CK**) via `crml_attack_catalog`.
- If an engine supports additional attack frameworks (e.g., CAPEC) or needs attack→attack crosswalks, that mapping logic/data is outside the CRML language contract.

Two important contracts are language-owned:

- **Portfolio bundle** (`crml_portfolio_bundle: "1.0"`): an inlined, filesystem-free input artifact.
- **Simulation result envelope** (`crml_simulation_result: "1.0"`): a stable output container for downstream tools/UIs.

## System-level data flow

```mermaid
flowchart TD
    DOC["CRML YAML/JSON"]
    ORGDATA["Org evidence<br/>(incident logs, telemetry)"]

    subgraph L["crml_lang (language/spec responsibility)<br/>Ends after validation + bundling"]
        LANG["crml_lang<br/>validate"]
        BUNDLE["crml_lang<br/>bundle"]
    end

    subgraph T["Tooling (engine/tool responsibility)<br/>Optional calibration step"]
        CAL["calibrate<br/>(fit/update scenario params)"]
    end

    subgraph E["crml_engine (engine responsibility)<br/>Planning + execution"]
        PIPE["crml_engine.pipeline<br/>plan"]
        ENG["crml_engine<br/>execute"]
    end

    subgraph W["web/ (UI responsibility)"]
        WEB[CRML Studio UI]
    end

    DOC --> LANG
    LANG -->|ValidationReport| TOOL[CLI/CI/Web tooling]

    ORGDATA -.-> CAL
    DOC -.-> CAL
    CAL -.->|updated CRML YAML/JSON| DOC

    DOC --> BUNDLE
    BUNDLE -->|CRPortfolioBundle| PIPE
    PIPE -->|PortfolioExecutionPlan| ENG
    ENG --> RES[SimulationResultEnvelope]
    RES --> WEB
```

## Ecosystem data flow

CRML is designed so that organizations can assemble *auditable, portable* input artifacts from common upstream sources, and so that any compliant engine can emit results in a shared format that downstream tools can visualize.

In practice:

- **Threat intelligence** produces or informs *scenario documents* (frequency, severity, narratives, assumptions).
- **Attack catalogs** provide stable attack-pattern identifiers and metadata (titles/urls/tags) that scenarios and tools can reference.
- **Organization evidence** (incident logs, internal loss data, telemetry) can be used by *calibration tools* to fit scenario parameters and reduce reliance on purely external priors.
- **Portfolios** describe the organization's relatively stable assets, business units, and exposure structure. They can be updated via internal tooling (e.g., CMDB/asset inventory imports), but the portfolio document remains the central reference.
- **Control catalogs** come from recognized authorities and frameworks (e.g., NIS, CIS) or can be commonly defined by the community. These catalogs define the canonical control set and their semantics.
- **Assessments** come from assessment/scan tools and audits. They capture which controls exist, how effective they are, and can optionally be used to populate or update the portfolio's control mapping.
- **Mappings** (control-to-control relationships) can come from public sources (e.g., Secure Controls Framework) and from community or organization-specific mapping work.

An additional (common) integration artifact is **attack-to-control mapping**:

- Tools/community datasets can map attack-pattern ids (from an attack catalog) to control ids (from a control catalog).
- CRML standardizes this as a first-class document type via `crml_attack_control_relationships`, so engines/tools can share mapping documents.

The language layer then provides a deterministic bundling step that inlines the referenced material into a self-contained `CRPortfolioBundle`, which can be handed to any risk engine without requiring filesystem access.

Engines are expected to return results using the **language-owned result envelope** (`SimulationResultEnvelope`). This creates a stable interface for any visualization tool (web UI, BI dashboards, reporting pipelines) to consume outputs without being coupled to a specific engine implementation.

```mermaid
flowchart LR
    TI["Threat intelligence<br/>feeds"] -->|publish| AC["Attack catalog<br/>CRAttackCatalog"]
    TI -->|publish/inform| S["Scenario documents<br/>CRScenario"]
    AC -.->|reference ids/metadata| S

    EVID["Organization evidence<br/>(incident logs, telemetry)"] -->|calibrate| CAL

    subgraph T2["Calibration tooling<br/>(engine/tool responsibility)"]
        CAL["calibrate<br/>(fit/update scenarios)"]
    end

    CAL -->|write back| S

    ORG["Organization asset inventory<br/>(relatively static)"] -->|generate| P["Portfolio document<br/>CRPortfolio"]
    TOOL["Tooling (e.g. SIEM)<br/>imports and updates assets"] -.->|optional| P

    AUTH["Recognized authorities<br/>NIS, CIS"] -->|publish| CC["Control catalog<br/>CRControlCatalog"]
    SCAN["Assessment and scan tools"] -->|generate| CA["Assessment catalog<br/>CRAssessment"]

    COMM["Community / org mappings"] -->|publish| CR["Control relationships pack<br/>CRControlRelationships"]

    MAP["Attack→control relationships<br/>CRAttackControlRelationships"]
    AC -.->|attack ids| MAP
    CC -.->|control ids| MAP
    MAP -.->|suggest relevant controls| S

    CC -.->|basis| CA
    CC -.->|ids| CR

    subgraph L2["crml_lang (language/spec responsibility)<br/>Ends after bundling"]
        B["Bundle step<br/>bundle_portfolio"]
        PB["CRPortfolioBundle<br/>inlined artifact"]
    end

    S --> B
    P --> B
    CC --> B
    CA --> B
    CR --> B
    MAP --> B
    B --> PB

    subgraph E2["Engines + tools (outside language responsibility)"]
        ENG["Risk engines<br/>engine A, engine B"]
        OUT["SimulationResultEnvelope<br/>standard contract"]
        VIZ["Visualization tools<br/>dashboards and reports"]
    end

    PB --> ENG
    ENG --> OUT
    OUT --> VIZ
```
