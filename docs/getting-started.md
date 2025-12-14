# Getting Started

This guide walks you from **zero** to running your **first CRML model**.

---

## 1. Install the CRML runtime

```bash
pip install crml-lang
```

Or, if you're working from the source repo:

```bash
git clone https://github.com/Faux16/crml.git
cd crml
pip install -e .
```

---

## 2. Create a minimal CRML model

Create `model.yaml`:

```yaml
crml: "1.1"

meta:
  name: "toy-model"
  description: "Minimal CRML example"

model:
  assets:
    cardinality: 1000

  frequency:
    model: poisson
    parameters:
      lambda: 0.2   # expected events per asset per year

  severity:
    model: lognormal
    parameters:
      mu: 10.0      # log-scale mean
      sigma: 1.0    # log-scale std
```

---

## 3. Validate the model

```bash
crml validate model.yaml
```

If the structure is correct, you should see:

```text
[OK] model.yaml is a valid CRML document.
```

---

## 4. Run a simulation

```bash
crml run model.yaml --runs 20000
```

Example output:

```text
=== CRML Simulation Results ===
EAL: 154320.42
VaR_95: 608123.77
VaR_99: 1123849.11
VaR_999: 3229912.88
```

---

## 5. Explore the model

```bash
crml explain model.yaml
```

This prints a human-readable summary of:

- assets
- frequency model
- severity model
- a short description

---

## 6. Next steps

- Read the **Specification** section to understand the CRML schema.
- Read the **Runtime** pages to see how the underlying mathematics works.
- Study the **Models & Examples** section to see QBER and FAIR baselines.
