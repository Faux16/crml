from __future__ import annotations

import importlib
import inspect

from pydantic import BaseModel


_MODULES_TO_CHECK = [
    # crml_lang models
    "crml_lang.models.scenario_model",
    "crml_lang.models.portfolio_model",
    "crml_lang.models.assessment_model",
    "crml_lang.models.control_catalog_model",
    "crml_lang.models.attack_catalog_model",
    "crml_lang.models.control_relationships_model",
    "crml_lang.models.control_ref",
    "crml_lang.models.coverage_model",
    "crml_lang.models.simulation_result",
    "crml_engine.pipeline.portfolio_planner",
    "crml_engine.models.fx_model",
    "crml_engine.models.result_model",
]


def _iter_pydantic_models(module) -> list[type[BaseModel]]:
    models: list[type[BaseModel]] = []
    for obj in vars(module).values():
        if not inspect.isclass(obj):
            continue
        if obj is BaseModel:
            continue
        if not issubclass(obj, BaseModel):
            continue
        if getattr(obj, "__module__", None) != module.__name__:
            continue
        models.append(obj)
    return models


def test_all_pydantic_fields_have_descriptions() -> None:
    missing: list[str] = []

    for module_name in _MODULES_TO_CHECK:
        module = importlib.import_module(module_name)
        for model_cls in _iter_pydantic_models(module):
            for field_name, field_info in model_cls.model_fields.items():
                desc = field_info.description
                if desc is None or not str(desc).strip():
                    missing.append(f"{module_name}.{model_cls.__name__}.{field_name}")

    assert not missing, "Missing Pydantic field descriptions:\n" + "\n".join(missing)
