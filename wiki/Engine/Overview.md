# Engine overview (`crml_engine`)

`crml_engine` is the reference execution engine for CRML.

It is responsible for:

- Executing CRML documents via Monte Carlo simulation.
- Deciding which models/algorithms are supported (engine-defined).
- Producing results (including JSON output) for tooling and integrations.

It is not responsible for defining portable document shapes and basic semantics — that is the job of `crml_lang`.

See also:

- Language responsibilities: [CRML Specification (Overview)](../Reference/CRML-Specification.md)
- CLI reference: [CLI](CLI.md)
- Engine APIs: [Python API](Python-API.md)
- Implemented features (tests-backed): [Capabilities](Capabilities/Supported-Models.md)
