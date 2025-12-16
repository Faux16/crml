# How-to: Add a New Probability Distribution

CRML is designed to be extensible. This guide explains how to add a new statistical distribution (e.g., Weibull, Beta, Student's t) to the simulation engine.

## Overview
Adding a distribution involves three steps:
1.  **Schema**: Update `crml_model.py` to allow the new parameters.
2.  **Engine**: Update `frequency.py` or `severity.py` to handle the sampling logic.
3.  **Testing**: Add a unit test to verify the distribution's behavior.

---

## Step 1: Update the Schema
File: `src/crml/models/crml_model.py`

Add the optional parameters required by your new distribution to `FrequencyParameters` or `SeverityParameters`.

**Example: Adding Weibull (shape separate from Gamma's shape)**
```python
class SeverityParameters(BaseModel):
    # ... existing fields ...
    weibull_shape: Optional[float] = None  # New parameter
    weibull_scale: Optional[float] = None
```
*(Note: You can often reuse generic names like `shape`, `scale`, `alpha`, `beta` if the semantics align)*

---

## Step 2: Implement Sampling Logic

### For Severity Distributions
File: `src/crml/simulation/severity.py`

Update `SeverityEngine.generate_severity`:

```python
    @classmethod
    def generate_severity(cls, sev_model, params, ...):
        # ...
        elif sev_model == 'weibull':
            # 1. Extract parameters
            a = float(params.shape) if params.shape else 1.0
            scale = float(params.scale) if params.scale else 1.0
            
            # 2. Sample (using numpy)
            # Weibull in numpy is scale * np.random.weibull(a)
            losses = scale * np.random.weibull(a, total_events)
            
            return losses
```

### For Frequency Distributions
File: `src/crml/simulation/frequency.py`

Update `FrequencyEngine.generate_frequency`. Remember to handle the `uniforms` argument if you want to support Copula-based correlations (requires implementing the Inverse CDF / PPF using `scipy.stats`).

```python
        elif freq_model == 'negative_binomial':
             # ... implementation ...
```

---

## Step 3: Verify

Create a test case in `tests/test_simulation_engine.py` or a new test file.

```python
def test_weibull_severity():
    schema = """
    crml: "1.1"
    meta: {name: "Weibull Test"}
    model:
      frequency: {model: poisson, parameters: {lambda: 1000}}
      severity: 
        model: weibull
        parameters: {shape: 2.0, scale: 500}
    """
    result = run_monte_carlo(schema)
    assert result.success
    # Check if mean approximately matches Weibull mean formula
    # Mean = scale * Gamma(1 + 1/shape)
    # 500 * Gamma(1.5) ~= 500 * 0.886 ~= 443
    assert 400 < result.metrics.eal < 500
```
