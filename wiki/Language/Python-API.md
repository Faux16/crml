# Language Python API (`crml_lang`)

`crml_lang` is the supported import surface for loading and validating CRML documents.

---

## Load and dump YAML

### Scenario

```python
from crml_lang import CRScenario

scenario = CRScenario.load_from_yaml("examples/scenarios/scenario-phishing.yaml")
print(scenario.meta.name)

yaml_text = scenario.dump_to_yaml_str()
```

### Portfolio

```python
from crml_lang import CRPortfolio

portfolio = CRPortfolio.load_from_yaml("examples/portfolios/portfolio.yaml")
print(portfolio.meta.name)
```

---

## Validate documents

### Validate any document type

```python
from crml_lang import validate_document

report = validate_document("examples/scenarios/scenario-phishing.yaml", source_kind="path")
print(report.render_text(source_label="scenario-phishing.yaml"))
```

### Validate portfolios (with semantic checks)

```python
from crml_lang import validate_portfolio

report = validate_portfolio("examples/portfolios/portfolio.yaml", source_kind="path")
if not report.ok:
    raise SystemExit(report.render_text(source_label="portfolio.yaml"))
```

Notes:

- `validate_document` detects the document type by top-level discriminator keys.
- Validation includes schema errors and semantic warnings.
