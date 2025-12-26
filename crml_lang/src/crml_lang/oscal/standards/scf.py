from __future__ import annotations

from .base import OscalControlTextOptions


def scf_control_text_options() -> OscalControlTextOptions:
    """SCF-specific mapping for OSCAL control text.

    SCF OSCAL catalogs often embed large maturity rubrics (`parts[].name == 'maturity'`).
    For CRML control catalogs we typically want a compact description:
    - statement prose (primary control statement)
    - objectives (criteria/checkpoints)

    We intentionally exclude maturity prose by default.
    """

    return OscalControlTextOptions(
        include_part_names={"statement", "objective"},
        include_control_prose=False,
        objective_heading="Objectives",
        bullet_objectives=True,
        include_objective_ids=True,
    )
