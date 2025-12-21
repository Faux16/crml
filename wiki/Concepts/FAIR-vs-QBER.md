# FAIR vs QBER

This page compares two common *styles* of cyber risk modeling and how they map to CRML.

- **FAIR-style** models often focus on decomposing loss event frequency and loss magnitude using expert-driven factor models.
- **QBER-style** models often emphasize a more explicit threat-action view and may include richer control-state and dependency structures.

CRML is flexible: both styles can be represented as scenario documents plus optional portfolio context.

---

## Mapping into CRML

In CRML terms:

- Frequency assumptions live in `crml_scenario.scenario.frequency`.
- Severity assumptions live in `crml_scenario.scenario.severity`.
- Exposure scaling is handled by portfolios via `scenario.frequency.basis` + portfolio asset binding.
- Controls can be referenced by scenarios and implemented/measured in portfolios.

See:

- [CRML Specification (Overview)](../Reference/CRML-Specification.md)
- [Best Practices](../Examples/Best-Practices.md)

---

## Reference engine status

Some features (e.g., correlated control-state sampling via copula) are supported by the reference engine and documented under:

- [Engine capabilities: Controls](../Engine/Capabilities/Controls.md)
