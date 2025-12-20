from __future__ import annotations

import io


def test_crml_lang_validate_ok(tmp_path) -> None:
    from crml_lang.cli import validate_to_text

    p = tmp_path / "scenario.yaml"
    p.write_text(
        """
crml_scenario: "1.0"
meta:
  name: "test-model"
scenario:
  frequency:
    basis: per_organization_per_year
    model: poisson
    parameters: {lambda: 0.5}
  severity:
    model: lognormal
    parameters: {mu: 10.0, sigma: 1.0}
""".lstrip(),
        encoding="utf-8",
    )

    stdout = io.StringIO()
    stderr = io.StringIO()
    code = validate_to_text(str(p), stdout=stdout, stderr=stderr)

    assert code == 0
    assert stderr.getvalue() == ""
    assert "ok" in stdout.getvalue().lower() or "valid" in stdout.getvalue().lower()


def test_crml_lang_validate_bad_yaml(tmp_path) -> None:
    from crml_lang.cli import validate_to_text

    p = tmp_path / "bad.yaml"
    p.write_text("not: [valid", encoding="utf-8")

    stdout = io.StringIO()
    stderr = io.StringIO()
    code = validate_to_text(str(p), stdout=stdout, stderr=stderr)

    assert code == 1
    assert stdout.getvalue() != ""
