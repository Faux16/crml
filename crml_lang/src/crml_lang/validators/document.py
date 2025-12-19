from __future__ import annotations

from typing import Any, Literal

from .common import ValidationMessage, ValidationReport, _load_input
from .scenario import validate as validate_scenario
from .portfolio import validate_portfolio
from .control_catalog import validate_control_catalog
from .assessment import validate_assessment
from .control_relationships import validate_control_relationships
from .attack_catalog import validate_attack_catalog
from .attack_control_relationships import validate_attack_control_relationships
from .portfolio_bundle import validate_portfolio_bundle


def _detect_kind(data: dict[str, Any]) -> str | None:
    """Best-effort CRML document kind detection.

    Detection is based on the presence of a top-level version key.
    """

    if "crml_scenario" in data:
        return "scenario"
    if "crml_portfolio" in data:
        return "portfolio"
    if "crml_control_catalog" in data:
        return "control_catalog"
    if "crml_attack_catalog" in data:
        return "attack_catalog"
    if "crml_assessment" in data:
        return "assessment"
    if "crml_control_relationships" in data:
        return "control_relationships"
    if "crml_attack_control_relationships" in data:
        return "attack_control_relationships"
    if "crml_portfolio_bundle" in data:
        return "portfolio_bundle"

    return None


def validate_document(
    source: str | dict[str, Any],
    *,
    source_kind: Literal["path", "yaml", "data"] | None = None,
    strict_model: bool = False,
) -> ValidationReport:
    """Validate any supported CRML document type.

    This is a small dispatcher that routes to the appropriate schema validator based on
    top-level version keys (e.g. `crml_scenario`, `crml_portfolio`, `crml_control_catalog`, ...).
    """

    data, io_errors = _load_input(source, source_kind=source_kind)
    if io_errors:
        return ValidationReport(ok=False, errors=io_errors, warnings=[])
    assert data is not None

    kind = _detect_kind(data)
    if kind is None:
        return ValidationReport(
            ok=False,
            errors=[
                ValidationMessage(
                    level="error",
                    source="semantic",
                    path="(root)",
                    message=(
                        "Unknown CRML document type. Expected one of: crml_scenario, crml_portfolio, "
                        "crml_control_catalog, crml_attack_catalog, crml_assessment, crml_control_relationships, "
                        "crml_attack_control_relationships, crml_portfolio_bundle."
                    ),
                )
            ],
            warnings=[],
        )

    if kind == "scenario":
        return validate_scenario(source, source_kind=source_kind, strict_model=strict_model)
    if kind == "portfolio":
        # Portfolio validator does not currently implement strict_model.
        return validate_portfolio(source, source_kind=source_kind)
    if kind == "control_catalog":
        return validate_control_catalog(source, source_kind=source_kind, strict_model=strict_model)
    if kind == "attack_catalog":
        return validate_attack_catalog(source, source_kind=source_kind, strict_model=strict_model)
    if kind == "assessment":
        return validate_assessment(source, source_kind=source_kind, strict_model=strict_model)
    if kind == "control_relationships":
        return validate_control_relationships(source, source_kind=source_kind, strict_model=strict_model)
    if kind == "attack_control_relationships":
        return validate_attack_control_relationships(source, source_kind=source_kind, strict_model=strict_model)
    if kind == "portfolio_bundle":
        return validate_portfolio_bundle(source, source_kind=source_kind, strict_model=strict_model)

    return ValidationReport(
        ok=False,
        errors=[
            ValidationMessage(
                level="error",
                source="semantic",
                path="(root)",
                message=f"Unsupported CRML document kind: {kind}",
            )
        ],
        warnings=[],
    )
