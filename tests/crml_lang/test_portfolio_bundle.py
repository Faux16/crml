from __future__ import annotations

from crml_lang import CRPortfolio, CRScenario, bundle_portfolio


def test_bundle_portfolio_inlines_scenario(tmp_path) -> None:
    scenario_path = tmp_path / "scenario.yaml"
    scenario_path.write_text(
        """
crml_scenario: "1.0"
meta:
  name: "Threat scenario"
scenario:
  frequency:
    basis: per_organization_per_year
    model: poisson
    parameters: {lambda: 0.5}
  severity:
    model: lognormal
    parameters: {mu: 10, sigma: 1}
""".lstrip(),
        encoding="utf-8",
    )

    portfolio_path = tmp_path / "portfolio.yaml"
    portfolio_path.write_text(
        f"""
crml_portfolio: "1.0"
meta:
  name: "Org portfolio"
portfolio:
  semantics:
    method: sum
  scenarios:
    - id: s1
      path: {scenario_path.name}
""".lstrip(),
        encoding="utf-8",
    )

    report = bundle_portfolio(str(portfolio_path), source_kind="path")
    assert report.ok is True
    assert report.bundle is not None
    assert report.bundle.crml_portfolio_bundle == "1.0"
    assert len(report.bundle.portfolio_bundle.scenarios) == 1
    assert (
      report.bundle.portfolio_bundle.scenarios[0].scenario.meta.name
      == "Threat scenario"
    )


def test_bundle_portfolio_model_mode_inlines_scenario() -> None:
    scenario = CRScenario.load_from_yaml_str(
        """
crml_scenario: "1.0"
meta:
  name: "Threat scenario"
scenario:
  frequency:
    basis: per_organization_per_year
    model: poisson
    parameters: {lambda: 0.5}
  severity:
    model: lognormal
    parameters: {mu: 10, sigma: 1}
""".lstrip()
    )

    portfolio = CRPortfolio.load_from_yaml_str(
        """
crml_portfolio: "1.0"
meta:
  name: "Org portfolio"
portfolio:
  semantics:
    method: sum
  scenarios:
    - id: s1
      path: scenario.yaml
""".lstrip()
    )

    report = bundle_portfolio(portfolio, source_kind="model", scenarios={"s1": scenario})
    assert report.ok is True
    assert report.bundle is not None
    assert len(report.bundle.portfolio_bundle.scenarios) == 1
    assert report.bundle.portfolio_bundle.scenarios[0].id == "s1"
    assert (
      report.bundle.portfolio_bundle.scenarios[0].scenario.meta.name
      == "Threat scenario"
    )
