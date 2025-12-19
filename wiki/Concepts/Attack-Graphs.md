# Attack Graphs

Attack graphs model multi-step attacker progression through a system.

CRML is **not** an attack-graph language. Instead, CRML is designed as a portable layer for:

- describing scenario frequency/severity assumptions,
- referencing attack catalogs (e.g. ATT&CK), and
- connecting those scenarios to portfolios and controls.

---

## How attack graphs relate to CRML

Typical integration patterns:

- Use an attack-graph tool to generate scenario candidates or calibrate scenario frequencies.
- Reference attack-pattern ids and metadata via `crml_attack_catalog` and `crml_attack_control_relationships`.
- Use CRML portfolios and controls to evaluate “what if we implement control X?” across multiple scenarios.

See:

- [Language schemas](../Reference/CRML-Schema.md)
- [CRML System Architecture](Architecture.md)
