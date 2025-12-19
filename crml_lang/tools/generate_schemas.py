from __future__ import annotations

import json
from pathlib import Path

from crml_lang.models.scenario_model import CRScenario
from crml_lang.models.assessment_model import CRAssessment
from crml_lang.models.control_catalog_model import CRControlCatalog
from crml_lang.models.attack_catalog_model import CRAttackCatalog
from crml_lang.models.attack_control_relationships_model import CRAttackControlRelationships
from crml_lang.models.control_relationships_model import CRControlRelationships
from crml_lang.models.portfolio_model import CRPortfolio
from crml_lang.models.portfolio_bundle import CRPortfolioBundle
from crml_lang.models.simulation_result import CRSimulationResult


def main() -> None:
    here = Path(__file__).resolve()
    schemas_dir = here.parents[1] / "src" / "crml_lang" / "schemas"
    schemas_dir.mkdir(parents=True, exist_ok=True)

    scenario_schema = CRScenario.model_json_schema()
    portfolio_schema = CRPortfolio.model_json_schema()
    assessment_schema = CRAssessment.model_json_schema()
    control_catalog_schema = CRControlCatalog.model_json_schema()
    attack_catalog_schema = CRAttackCatalog.model_json_schema()
    attack_control_relationships_schema = CRAttackControlRelationships.model_json_schema()
    control_relationships_schema = CRControlRelationships.model_json_schema()
    portfolio_bundle_schema = CRPortfolioBundle.model_json_schema()
    simulation_result_schema = CRSimulationResult.model_json_schema()

    (schemas_dir / "crml-scenario-schema.json").write_text(
        json.dumps(scenario_schema, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (schemas_dir / "crml-portfolio-schema.json").write_text(
        json.dumps(portfolio_schema, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (schemas_dir / "crml-assessment-schema.json").write_text(
        json.dumps(assessment_schema, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    (schemas_dir / "crml-control-catalog-schema.json").write_text(
        json.dumps(control_catalog_schema, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    (schemas_dir / "crml-attack-catalog-schema.json").write_text(
        json.dumps(attack_catalog_schema, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    (schemas_dir / "crml-attack-control-relationships-schema.json").write_text(
        json.dumps(attack_control_relationships_schema, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    (schemas_dir / "crml-control-relationships-schema.json").write_text(
        json.dumps(control_relationships_schema, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    (schemas_dir / "crml-portfolio-bundle-schema.json").write_text(
        json.dumps(portfolio_bundle_schema, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    (schemas_dir / "crml-simulation-result-schema.json").write_text(
        json.dumps(simulation_result_schema, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote schemas to {schemas_dir}")


if __name__ == "__main__":
    main()
