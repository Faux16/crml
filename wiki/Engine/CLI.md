# Engine CLI (crml)

The `crml` command is installed by `crml-engine`.

## Validate

```bash
crml validate model.yaml
```

Exit code is `0` if valid, `1` if not.

## Simulate

```bash
crml simulate model.yaml --runs 10000
```

Options:
- `-n, --runs`: number of Monte Carlo runs (default: 10000)
- `-s, --seed`: random seed
- `-f, --format`: `text` or `json`
- `--fx-config`: path to an FX config YAML file

## Explain

```bash
crml explain model.yaml
```

## Alias

`crml run` is an alias for `crml simulate` with text output.
