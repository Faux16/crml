# CRML System Architecture

CRML is organized into three layers:

- **Language/spec (`crml_lang`)**: schemas, models, validation, YAML IO
- **Runtime/engine (`crml_engine`)**: CLI + simulation runtime + portfolio execution + result serialization
- **Web UI (`web/`)**: CRML Studio (Next.js UI + API routes that call the CLI/runtime)

For the detailed architecture, see:

- [Architecture-Language](Architecture-Language)
- [Architecture-Engine](Architecture-Engine)

## Document types

- Scenario documents: `crml_scenario: "1.0"` (top-level `scenario:`)
- Portfolio documents: `crml_portfolio: "1.0"` (top-level `portfolio:`; if `portfolio.control_assessments` is used, `portfolio.control_catalogs` must also be provided)
- Control catalog packs: `crml_control_catalog: "1.0"` (top-level `catalog:`)
- Control assessment packs: `crml_control_assessment: "1.0"` (top-level `assessment:`)
- FX config documents: `crml_fx_config: "1.0"` (top-level `base_currency`, `output_currency`, `rates`, optional `as_of`; engine-owned config document)
- Portfolio bundle artifacts: `crml_portfolio_bundle: "1.0"` (top-level `portfolio_bundle:`)
- Simulation result artifacts: `crml_simulation_result: "1.0"` (top-level `result:`)

## System-level data flow

```mermaid
flowchart TD
    DOC[CRML YAML/JSON] --> LANG[crml_lang\nvalidate]
    LANG -->|ValidationReport| TOOL[CLI/CI/Web tooling]

    DOC --> BUNDLE[crml_lang\nbundle]
    BUNDLE -->|CRPortfolioBundle| PIPE[crml_engine.pipeline\nplan]
    PIPE -->|PortfolioExecutionPlan| ENG[crml_engine\nexecute]
    ENG --> RES[SimulationResultEnvelope]
    RES --> WEB[CRML Studio UI]
```

## Ecosystem data flow

CRML is designed so that organizations can assemble *auditable, portable* input artifacts from common upstream sources, and so that any compliant engine can emit results in a shared format that downstream tools can visualize.

In practice:

- **Threat intelligence** produces or informs *scenario documents* (frequency, severity, narratives, assumptions).
- **Portfolios** describe the organization's relatively stable assets, business units, and exposure structure. They can be updated via internal tooling (e.g., CMDB/asset inventory imports), but the portfolio document remains the central reference.
- **Control catalogs** come from recognized authorities and frameworks (e.g., NIS, CIS) or can be commonly defined by the community. These catalogs define the canonical control set and their semantics.
- **Control assessments** come from assessment/scan tools and audits. They capture which controls exist, how effective they are, and can optionally be used to populate or update the portfolio's control mapping.

The language layer then provides a deterministic bundling step that inlines the referenced material into a self-contained `CRPortfolioBundle`, which can be handed to any risk engine without requiring filesystem access.

Engines are expected to return results using the **language-owned result envelope** (`SimulationResultEnvelope`). This creates a stable interface for any visualization tool (web UI, BI dashboards, reporting pipelines) to consume outputs without being coupled to a specific engine implementation.

```mermaid
flowchart LR
    TI["Threat intelligence<br/>feeds"] -->|publish| S["Scenario documents<br/>CRScenario"]

    ORG["Organization asset inventory<br/>(relatively static)"] --> P["Portfolio document<br/>CRPortfolio"]
    TOOL["Tooling (e.g. SIEM)<br/>imports and updates"] -.->|optional| P

    AUTH["Recognized authorities<br/>NIS, CIS"] -->|publish| CC["Control catalog pack<br/>CRControlCatalog"]
    SCAN["Assessment and scan tools"] --> CA["Control assessment pack<br/>CRControlAssessment"]

    CC -.->|basis| CA

    S --> B["Bundle step<br/>bundle_portfolio"]
    P --> B
    CC --> B
    CA --> B

    B --> PB["CRPortfolioBundle<br/>inlined artifact"]

    PB --> ENG["Risk engines<br/>engine A, engine B"]
    ENG --> OUT["SimulationResultEnvelope<br/>standard contract"]
    OUT --> VIZ["Visualization tools<br/>dashboards and reports"]
```
