# Calibrate from data

Calibration converts organization-specific evidence (incident losses, telemetry-derived estimates) into scenario parameters.

CRML treats calibration as **engine/tool responsibility**; the language defines where calibrated parameters live in documents.

---

## Lognormal calibration from `single_losses`

The reference engine supports calibrating lognormal parameters from empirical single-event losses.

### Python

```python
from crml_engine.runtime import calibrate_lognormal_from_single_losses
from crml_engine.models.fx_model import get_default_fx_config

fx = get_default_fx_config()
mu, sigma = calibrate_lognormal_from_single_losses(
    single_losses=[12000, 18000, 25000, 9000, 40000],
    currency="USD",
    base_currency=fx.base_currency,
    fx_config=fx,
)
print(mu, sigma)
```

### Scenario YAML (engine-defined)

Some engines may also accept `single_losses` inside the lognormal parameters and calibrate automatically.

See: [Runtime (Severity)](../Concepts/Runtime-Severity.md)
