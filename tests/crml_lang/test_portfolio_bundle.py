from __future__ import annotations

from crml_lang.api import CRPortfolio, CRScenario
from crml_lang.bundling import bundle_portfolio
from crml_lang.validators import validate_document


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


def test_bundle_portfolio_model_mode_auto_resolves_scenario_paths(tmp_path) -> None:
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

    portfolio = CRPortfolio.load_from_yaml(str(portfolio_path))
    report = bundle_portfolio(portfolio, source_kind="model", base_dir=str(tmp_path))
    assert report.ok is True
    assert report.bundle is not None
    assert len(report.bundle.portfolio_bundle.scenarios) == 1
    assert report.bundle.portfolio_bundle.scenarios[0].id == "s1"
    assert report.bundle.portfolio_bundle.scenarios[0].scenario.meta.name == "Threat scenario"


def test_bundle_portfolio_model_mode_manual_requires_scenarios_when_disabled(tmp_path) -> None:
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

    portfolio = CRPortfolio.load_from_yaml(str(portfolio_path))
    report = bundle_portfolio(
        portfolio,
        source_kind="model",
        base_dir=str(tmp_path),
        resolve_references=False,
    )
    assert report.ok is False
    assert any("resolve_references=False requires `scenarios`" in e.message for e in report.errors)


def test_validate_portfolio_bundle_errors_when_scenario_controls_have_no_posture_or_mapping() -> None:
    bundle = {
        "crml_portfolio_bundle": "1.0",
        "portfolio_bundle": {
            "portfolio": {
                "crml_portfolio": "1.0",
                "meta": {"name": "bundle-portfolio"},
                "portfolio": {
                    "semantics": {"method": "sum"},
                    "assets": [{"name": "endpoints", "cardinality": 10}],
                    "scenarios": [{"id": "s1", "path": "scenario.yaml"}],
                },
            },
            "scenarios": [
                {
                    "id": "s1",
                    "scenario": {
                        "crml_scenario": "1.0",
                        "meta": {"name": "inlined-scenario"},
                        "scenario": {
                            "frequency": {
                                "basis": "per_organization_per_year",
                                "model": "poisson",
                                "parameters": {"lambda": 0.5},
                            },
                            "severity": {
                                "model": "lognormal",
                                "parameters": {"median": 1000, "sigma": 1.0, "currency": "USD"},
                            },
                            "controls": ["cisv8:4.2"],
                        },
                    },
                }
            ],
            "assessments": [],
            "control_relationships": [],
            "control_catalogs": [],
            "attack_catalogs": [],
            "attack_control_relationships": [],
        },
    }

    report = validate_document(bundle, source_kind="data")
    assert report.ok is False
    assert any("reference controls" in e.message for e in report.errors)


def test_validate_portfolio_bundle_errors_on_control_relationship_targets_not_in_posture() -> None:
    bundle = {
        "crml_portfolio_bundle": "1.0",
        "portfolio_bundle": {
            "portfolio": {
                "crml_portfolio": "1.0",
                "meta": {"name": "bundle-portfolio"},
                "portfolio": {
                    "semantics": {"method": "sum"},
                    "assets": [{"name": "endpoints", "cardinality": 10}],
                    "scenarios": [{"id": "s1", "path": "scenario.yaml"}],
                },
            },
            "scenarios": [
                {
                    "id": "s1",
                    "scenario": {
                        "crml_scenario": "1.0",
                        "meta": {"name": "inlined-scenario"},
                        "scenario": {
                            "frequency": {
                                "basis": "per_organization_per_year",
                                "model": "poisson",
                                "parameters": {"lambda": 0.5},
                            },
                            "severity": {
                                "model": "lognormal",
                                "parameters": {"median": 1000, "sigma": 1.0, "currency": "USD"},
                            },
                            "controls": ["cisv8:4.2"],
                        },
                    },
                }
            ],
            "assessments": [
                {
                    "crml_assessment": "1.0",
                    "meta": {"name": "assess"},
                    "assessment": {
                        "framework": "custom",
                        "assessments": [
                            {"id": "cap:edr", "implementation_effectiveness": 0.8},
                        ],
                    },
                }
            ],
            "control_relationships": [
                {
                    "crml_control_relationships": "1.0",
                    "meta": {"name": "rels"},
                    "relationships": {
                        "relationships": [
                            {
                                "source": "cisv8:4.2",
                                "targets": [
                                    {"target": "cap:edr", "overlap": {"weight": 1.0}},
                                    {"target": "cap:missing", "overlap": {"weight": 0.5}},
                                ],
                            }
                        ]
                    },
                }
            ],
            "control_catalogs": [],
            "attack_catalogs": [],
            "attack_control_relationships": [],
        },
    }

    report = validate_document(bundle, source_kind="data")
    assert report.ok is False
    assert any(
        "target control id" in e.message and "cap:missing" in e.message for e in report.errors
    )


def test_validate_portfolio_bundle_errors_when_portfolio_references_assessments_but_bundle_inlines_none() -> None:
    bundle = {
        "crml_portfolio_bundle": "1.0",
        "portfolio_bundle": {
            "portfolio": {
                "crml_portfolio": "1.0",
                "meta": {"name": "bundle-portfolio"},
                "portfolio": {
                    "semantics": {"method": "sum"},
                    "assets": [{"name": "endpoints", "cardinality": 10}],
                    "assessments": ["control-assessment.yaml"],
                    "scenarios": [{"id": "s1", "path": "scenario.yaml"}],
                },
            },
            "scenarios": [
                {
                    "id": "s1",
                    "scenario": {
                        "crml_scenario": "1.0",
                        "meta": {"name": "inlined-scenario"},
                        "scenario": {
                            "frequency": {
                                "basis": "per_organization_per_year",
                                "model": "poisson",
                                "parameters": {"lambda": 0.5},
                            },
                            "severity": {
                                "model": "lognormal",
                                "parameters": {"median": 1000, "sigma": 1.0, "currency": "USD"},
                            },
                        },
                    },
                }
            ],
            "assessments": [],
            "control_relationships": [],
            "control_catalogs": [],
            "attack_catalogs": [],
            "attack_control_relationships": [],
        },
    }

    report = validate_document(bundle, source_kind="data")
    assert report.ok is False
    assert any(
        "Portfolio references 'portfolio.assessments'" in e.message and "control-assessment.yaml" in e.message
        for e in report.errors
    )
