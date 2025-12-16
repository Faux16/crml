# Install the engine package (crml_engine)

Install the reference engine:

```bash
pip install crml-engine
```

This also installs `crml-lang` as a dependency.

## Verify

```bash
crml --help
```

## Run a quick simulation

```bash
crml simulate examples/scenarios/data-breach-simple.yaml --runs 10000
```
