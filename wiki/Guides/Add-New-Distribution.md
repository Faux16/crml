# Add new distribution (engine developer guide)

This guide explains how to add a new frequency or severity model to the **reference engine**.

---

## 1) Choose a model identifier

Model identifiers are engine-defined strings used in scenario documents:

- `scenario.frequency.model`
- `scenario.severity.model`

---

## 2) Implement generation logic

- Frequency models live in `crml_engine/src/crml_engine/simulation/frequency.py`
- Severity models live in `crml_engine/src/crml_engine/simulation/severity.py`

---

## 3) Register support

The engine rejects unknown models in `_validate_supported_models`.

See: `crml_engine/src/crml_engine/simulation/engine.py`

---

## 4) Add tests

Add tests under `tests/crml_engine/` to lock in behavior.

---

## 5) Update docs

- Add the model to: [Engine capabilities: Supported models](../Engine/Capabilities/Supported-Models.md)
- If needed, update the conceptual pages under [Concepts](../Concepts/Architecture.md)
