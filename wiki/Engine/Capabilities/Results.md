# Engine capabilities: Results

The reference engine exposes two result representations:

- **Engine-native**: `crml_engine.models.result_model.SimulationResult`
- **Engine-agnostic result document**: `crml_lang.models.simulation_result.CRSimulationResult` (`crml_simulation_result: "1.0"`)

---

## Engine-native result (`SimulationResult`)

The CLI (`crml simulate ...`) prints a formatted view of this result (or JSON via `--format json`).

Fields (high level):

- `success: bool`
- `metrics`: EAL, VaR, min/max/median/std
- `distribution`: histogram bins/counts and optional raw samples (engine-defined)
- `metadata`: run count, currency code/symbol, model meta, runtime ms, and some engine-specific fields
- `errors: list[str]`

Model definition: [crml_engine/src/crml_engine/models/result_model.py](../../../crml_engine/src/crml_engine/models/result_model.py)
Model definition: `crml_engine/src/crml_engine/models/result_model.py`

---

## Result document (`CRSimulationResult`)

The envelope lives in `crml_lang` so engines and UIs can share a stable contract.

- Document discriminator: `crml_simulation_result: "1.0"`
- Payload: `result` with `engine`, `run`, `inputs`, `units`, and structured `measures` + `artifacts`

Model definition: [crml_lang/src/crml_lang/models/simulation_result.py](../../../crml_lang/src/crml_lang/models/simulation_result.py)
Model definition: `crml_lang/src/crml_lang/models/simulation_result.py`

---

## Currency and units

The reference engine reports currency using the FX config output currency:

- `Metadata.currency_code` and `Metadata.currency` (symbol)
- Envelope `units.currency.code` and optional `units.currency.symbol`

FX configuration is engine-owned; see:

- [Language/Schemas/FX-Config](../../Language/Schemas/FX-Config.md)
- [Multi-Currency Support](../../Multi-Currency-Support.md)
