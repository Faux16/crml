# Control effectiveness

Control effectiveness is represented in CRML as a combination of:

- **Implementation effectiveness** (how well the control works when it is up)
- **Coverage** (what fraction of relevant scope it covers)
- **Reliability** (probability the control is “up” in a given run)
- **Affects** surface (`frequency`, `severity`, or `both`)

Scenarios reference controls by id; portfolios provide the implementation/measurement values.

---

## Reference engine behavior

The reference engine applies controls as multiplicative reductions (per run):

- reduction = `effectiveness × coverage × state`
- multiplier = `1 - reduction`

See:

- [Engine capabilities: Controls](Engine/Capabilities/Controls.md)
- [Engine capabilities: Portfolio execution](Engine/Capabilities/Portfolio-Execution.md)

---

## Language contracts

The portable document fields are defined in the schemas:

- [Scenario schema](Language/Schemas/Scenario.md)
- [Portfolio schema](Language/Schemas/Portfolio.md)
