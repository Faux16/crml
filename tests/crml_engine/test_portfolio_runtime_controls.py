from __future__ import annotations

from crml_engine.runtime import run_portfolio_bundle_simulation


def test_portfolio_runtime_runs_with_control_state_copula(tmp_path):
    scenario_yaml = """
crml_scenario: "1.0"
meta:
  name: "Scenario"
scenario:
  controls:
    - "cap:edr"
    - "cap:mfa"
  frequency:
    basis: per_organization_per_year
    model: poisson
    parameters: {lambda: 5.0}
  severity:
    model: lognormal
    parameters: {median: 1000, sigma: 0.5}
""".lstrip()

    bundle_path = tmp_path / "bundle.yaml"
    bundle_path.write_text(
        f"""
crml_portfolio_bundle: "1.0"
portfolio_bundle:
  portfolio:
    crml_portfolio: "1.0"
    meta:
      name: "Portfolio"
    portfolio:
      semantics:
        method: sum
      controls:
        - id: "cap:edr"
          implementation_effectiveness: 0.6
          coverage: {{value: 1.0, basis: applications}}
          reliability: 0.8
          affects: frequency
        - id: "cap:mfa"
          implementation_effectiveness: 0.7
          coverage: {{value: 0.9, basis: applications}}
          reliability: 0.9
          affects: frequency
      dependency:
        copula:
          type: gaussian
          structure: toeplitz
          rho: 0.65
          targets:
            - control:cap:edr:state
            - control:cap:mfa:state
      scenarios:
        - id: s1
          path: scenario.yaml
  scenarios:
    - id: s1
      scenario:
{'        ' + scenario_yaml.rstrip().replace('\n', '\n        ')}
""".lstrip(),
        encoding="utf-8",
    )

    res = run_portfolio_bundle_simulation(str(bundle_path), source_kind="path", n_runs=5000, seed=42)
    assert res.success is True
    assert res.metrics is not None
    assert res.metrics.eal is not None
    assert res.metrics.eal > 0
