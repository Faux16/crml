from __future__ import annotations

import io


def test_crml_lang_bundle_portfolio_to_yaml(tmp_path) -> None:
    from crml_lang.cli import bundle_portfolio_to_yaml

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

    out_path = tmp_path / "bundle.yaml"
    stdout = io.StringIO()
    stderr = io.StringIO()

    code = bundle_portfolio_to_yaml(
        str(portfolio_path),
        str(out_path),
        stdout=stdout,
        stderr=stderr,
    )

    assert code == 0
    assert stderr.getvalue() == ""
    assert out_path.exists() is True
    assert "Wrote" in stdout.getvalue()
