from __future__ import annotations

import json
from pathlib import Path

from crml_lang.models.crml_model import CRScenarioSchema
from crml_lang.models.control_assessment_model import CRControlAssessmentSchema
from crml_lang.models.portfolio_model import CRPortfolioSchema


def main() -> None:
    here = Path(__file__).resolve()
    schemas_dir = here.parents[1] / "src" / "crml_lang" / "schemas"
    schemas_dir.mkdir(parents=True, exist_ok=True)

    scenario_schema = CRScenarioSchema.model_json_schema()
    portfolio_schema = CRPortfolioSchema.model_json_schema()
    control_assessment_schema = CRControlAssessmentSchema.model_json_schema()

    (schemas_dir / "crml-scenario-schema.json").write_text(
        json.dumps(scenario_schema, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (schemas_dir / "crml-portfolio-schema.json").write_text(
        json.dumps(portfolio_schema, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (schemas_dir / "crml-control-assessment-schema.json").write_text(
        json.dumps(control_assessment_schema, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote schemas to {schemas_dir}")


if __name__ == "__main__":
    main()
