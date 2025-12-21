import pytest
from unittest.mock import patch
import sys
from crml_engine.cli import main

def test_cli_no_args():
    with patch.object(sys, 'argv', ['crml']):
        with pytest.raises(SystemExit) as cm:
            main()
        assert cm.value.code == 1

def test_cli_validate_success(valid_crml_file):
    with patch.object(sys, 'argv', ['crml', 'validate', valid_crml_file]):
        with pytest.raises(SystemExit) as cm:
            main()
        assert cm.value.code == 0


def test_cli_validate_failure(tmp_path):
    p = tmp_path / "invalid.yaml"
    p.write_text("not: [valid", encoding="utf-8")
    with patch.object(sys, 'argv', ['crml', 'validate', str(p)]):
        with pytest.raises(SystemExit) as cm:
            main()
        assert cm.value.code == 1

def test_cli_explain_success(valid_crml_file):
    with patch.object(sys, 'argv', ['crml', 'explain', valid_crml_file]):
        with pytest.raises(SystemExit) as cm:
            main()
        assert cm.value.code == 0


def test_cli_bundle_portfolio_writes_bundle(tmp_path) -> None:
        scenario_path = tmp_path / "scenario.yaml"
        scenario_path.write_text(
                """
crml_scenario: \"1.0\"
meta:
    name: \"Threat scenario\"
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
crml_portfolio: \"1.0\"
meta:
    name: \"Org portfolio\"
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

        with patch.object(sys, 'argv', ['crml', 'bundle-portfolio', str(portfolio_path), str(out_path)]):
                with pytest.raises(SystemExit) as cm:
                        main()
                assert cm.value.code == 0

        assert out_path.exists() is True
        text = out_path.read_text(encoding="utf-8")
        assert "crml_portfolio_bundle" in text
        assert "portfolio_bundle:" in text
