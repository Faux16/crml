from __future__ import annotations

from typing import Any, Literal

from .common import ValidationMessage, ValidationReport, _load_input
from .scenario import validate as validate_scenario
from .portfolio import validate_portfolio
from .control_catalog import validate_control_catalog
from .control_assessment import validate_control_assessment
from .control_relationships import validate_control_relationships


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
    if "crml_control_assessment" in data:
        return "control_assessment"
    if "crml_control_relationships" in data:
        return "control_relationships"

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
                        "crml_control_catalog, crml_control_assessment, crml_control_relationships."
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
    if kind == "control_assessment":
        return validate_control_assessment(source, source_kind=source_kind, strict_model=strict_model)
    if kind == "control_relationships":
        return validate_control_relationships(source, source_kind=source_kind, strict_model=strict_model)

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
