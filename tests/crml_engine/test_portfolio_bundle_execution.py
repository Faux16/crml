from __future__ import annotations

from crml_engine.runtime import run_portfolio_bundle_simulation


def test_run_portfolio_bundle_simulation_from_yaml_str() -> None:
    bundle_yaml = """
crml_portfolio_bundle: "1.0"
portfolio_bundle:
  portfolio:
    crml_portfolio: "1.0"
    meta:
      name: "bundle-portfolio"
    portfolio:
      semantics:
        method: sum
      assets:
        - name: endpoints
          cardinality: 10
      scenarios:
        - id: s1
          path: scenario.yaml

  scenarios:
    - id: s1
      weight: 1.0
      source_path: scenario.yaml
      scenario:
        crml_scenario: "1.0"
        meta:
          name: "inlined-scenario"
        scenario:
          frequency:
            basis: per_organization_per_year
            model: poisson
            parameters: {lambda: 0.5}
          severity:
            model: lognormal
            parameters: {median: 1000, sigma: 1.0, currency: USD}

  # Minimal assessment so the planner can resolve scenario controls when present.
  assessments: []
""".lstrip()

    res = run_portfolio_bundle_simulation(bundle_yaml, source_kind="yaml", n_runs=200, seed=123)
    assert res.success is True
    assert res.metrics is not None
    assert res.distribution is not None
