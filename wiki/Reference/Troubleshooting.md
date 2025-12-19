# Troubleshooting

## `crml` command not found

- Ensure you installed the engine package: `pip install crml-engine`
- Verify: `crml --help`

## Validation fails but YAML looks fine

- Run `crml validate <file>` to get the exact path and error.
- Confirm the top-level discriminator exists (e.g., `crml_scenario: "1.0"`).

See: [Validation](../Language/Validation.md)

## Simulation succeeds but results look wrong

- Start with fewer runs to iterate (`--runs 1000`), then increase to stabilize percentiles.
- Confirm whether frequency basis is `per_organization_per_year` vs `per_asset_unit_per_year`.

See: [Runtime (Frequency)](../Concepts/Runtime-Frequency.md)

## Multi-currency conversion surprises

- Confirm you are using an FX config (`--fx-config ...`) and that your rates are relative to `base_currency`.

See: [Multi-Currency Support](../Multi-Currency-Support.md)
