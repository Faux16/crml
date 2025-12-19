# Language overview (`crml_lang`)

`crml_lang` defines the **portable CRML language contract**:

- Document schemas (JSON Schema generated from Pydantic models)
- YAML load/dump helpers
- Validation (schema + semantic checks)
- Engine-agnostic interchange models (e.g., result envelope)

Engines (like `crml_engine`) decide which modeling algorithms are supported and how to execute them.

See: [CRML Specification (Overview)](../Reference/CRML-Specification.md)

---

## Document types

CRML is document-oriented. Common document discriminators include:

- `crml_scenario: "1.0"`
- `crml_portfolio: "1.0"`
- `crml_control_catalog: "1.0"`
- `crml_assessment: "1.0"`
- `crml_control_relationships: "1.0"`
- `crml_attack_catalog: "1.0"`
- `crml_attack_control_relationships: "1.0"`
- `crml_portfolio_bundle: "1.0"`
- `crml_simulation_result: "1.0"`

Schema docs live under: [Language/Schemas](Schemas/Scenario.md)
