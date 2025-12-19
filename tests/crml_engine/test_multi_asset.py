from __future__ import annotations
from crml_engine.pipeline import plan_portfolio
from crml_engine.simulation.engine import run_monte_carlo


def test_multi_asset_simulation_uses_portfolio_assets_for_cardinality(tmp_path):
    """True multi-asset test: assets live in the portfolio.

    We define a scenario with frequency basis `per_asset_unit_per_year`.
    The portfolio binds that scenario to two assets with cardinalities 10 and 5.
    The simulation should therefore use total cardinality=15, which scales
    Poisson(lambda) to Poisson(lambda * 15).

    Frequency: Poisson(2.0 * 15)
    Severity: Lognormal(median=1000, sigma=0.5)
    Mean Severity ~= 1000 * exp(0.5^2/2) = 1000 * exp(0.125) ~= 1133
    Expected Annual Loss ~= (2.0 * 15) * 1133 = 33990
    """

    scenario_path = tmp_path / "scenario.yaml"
    scenario_path.write_text(
        """
crml_scenario: "1.0"
meta:
  name: "Per-asset-unit scenario"
scenario:
  frequency:
    basis: per_asset_unit_per_year
    model: "poisson"
    parameters:
      lambda: 2.0
  severity:
    model: "lognormal"
    parameters:
      median: 1000
      sigma: 0.5
""".lstrip(),
        encoding="utf-8",
    )

    portfolio_path = tmp_path / "portfolio.yaml"
    portfolio_path.write_text(
        f"""
crml_portfolio: "1.0"
meta:
  name: "Multi-asset portfolio"
portfolio:
  assets:
    - name: a1
      cardinality: 10
    - name: a2
      cardinality: 5
  semantics:
    method: sum
  scenarios:
    - id: s1
      path: {scenario_path.name}
      binding:
        applies_to_assets: [a1, a2]
""".lstrip(),
        encoding="utf-8",
    )

    report = plan_portfolio(str(portfolio_path), source_kind="path")
    assert report.ok is True
    assert report.plan is not None
    assert report.plan.scenarios[0].cardinality == 15

    scenario_yaml = scenario_path.read_text(encoding="utf-8")
    result = run_monte_carlo(
        scenario_yaml,
        n_runs=20000,
        seed=42,
        cardinality=report.plan.scenarios[0].cardinality,
    )

    assert result.success, f"Simulation failed: {result.errors}"

    expected_eal = 33990.0
    margin = expected_eal * 0.05  # 5% Monte Carlo tolerance
    assert expected_eal - margin <= result.metrics.eal <= expected_eal + margin


def test_fallback_to_global_severity():
    """
    Scenario-only schema always uses a single global severity.
    This test ensures the engine runs with a valid global severity.
    """
    yaml_fallback = """
    crml_scenario: "1.0"
    meta: {name: "Fallback Test"}
    scenario:
      frequency:
        basis: per_organization_per_year
        model: "poisson"
        parameters: {lambda: 10}
      severity:
        model: "lognormal"
        parameters: {median: 50, sigma: 0.1}
    """
    result = run_monte_carlo(yaml_fallback, n_runs=1000, seed=42)
    assert result.success
    # Should run with global severity
    assert result.metrics.eal > 0
