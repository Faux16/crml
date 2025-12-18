from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from .scenario_model import AttckId, Meta


class AttackCatalogEntry(BaseModel):
    """Portable metadata about an ATT&CK (or similar) attack-pattern id.

    Important: do not embed copyrighted framework text here.
    Keep this to identifiers and tool-friendly metadata.
    """

    id: AttckId = Field(..., description="Canonical unique attack pattern id present in this catalog.")
    title: Optional[str] = Field(None, description="Optional short human-readable title for the attack pattern.")
    url: Optional[str] = Field(None, description="Optional URL for additional reference material.")
    tags: Optional[List[str]] = Field(None, description="Optional list of tags for grouping/filtering.")
    kill_chain_phases: Optional[List[str]] = Field(
        None,
        description=(
            "Optional STIX kill chain phases, expressed as strings. "
            "Recommended format is '<kill_chain_name>:<phase_name>' (e.g. 'mitre-attack:execution')."
        ),
    )


class AttackCataloge(BaseModel):
    id: Optional[str] = Field(None, description="Optional identifier for this cataloge (organization-owned).")
    framework: str = Field(
        ..., description="Free-form framework label for humans/tools. Example: 'MITRE ATT&CK Enterprise'."
    )
    attacks: List[AttackCatalogEntry] = Field(..., description="List of attack pattern catalog entries.")


class CRAttackCatalogSchema(BaseModel):
    crml_attack_catalog: Literal["1.0"] = Field(
        ..., description="Attack catalog document version identifier."
    )
    meta: Meta = Field(..., description="Document metadata (name, description, tags, etc.).")
    catalog: AttackCataloge = Field(..., description="The attack cataloge payload.")

    model_config: ConfigDict = ConfigDict(populate_by_name=True)
