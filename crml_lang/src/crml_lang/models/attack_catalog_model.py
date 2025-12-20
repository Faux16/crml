from __future__ import annotations

from typing import Annotated, List, Literal, Optional, Set

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .scenario_model import Meta


AttackId = Annotated[
    str,
    Field(
        min_length=1,
        max_length=256,
        pattern=r"^[a-z][a-z0-9_-]{0,31}:[^\s]{1,223}$",
        description=(
            "Attack identifier in canonical namespaced form 'namespace:key' (no whitespace). "
            "The namespace is expected to match the attack catalog's catalog.id."
        ),
    ),
]


AttackKind = Literal[
    # MITRE ATT&CK
    "tactic",
    "technique",
    "sub-technique",
    # CAPEC
    "attack-pattern",
    # Kill chains
    "phase",
    # NIST CSF
    "function",
    "category",
    "subcategory",
    # Diamond model vocabulary
    "role",
    "event",
]


def _ensure_in_namespace(*, entry_id: str, value: str, prefix: str, field: str) -> None:
    if not value.startswith(prefix):
        raise ValueError(
            f"Attack entry '{entry_id}' has {field} '{value}' outside catalog namespace '{prefix}'"
        )


def _ensure_ref_exists(*, entry_id: str, ref_id: str, entry_ids: Set[str], field: str) -> None:
    if ref_id not in entry_ids:
        raise ValueError(
            f"Attack entry '{entry_id}' references missing {field} id '{ref_id}'"
        )


def _validate_entry_refs(*, entry: "AttackCatalogEntry", prefix: str, entry_ids: Set[str]) -> None:
    _ensure_in_namespace(entry_id=entry.id, value=entry.id, prefix=prefix, field="id")

    if entry.parent is not None:
        _ensure_in_namespace(entry_id=entry.id, value=entry.parent, prefix=prefix, field="parent")
        _ensure_ref_exists(entry_id=entry.id, ref_id=entry.parent, entry_ids=entry_ids, field="parent")

    if entry.phases is not None:
        for phase_id in entry.phases:
            _ensure_in_namespace(entry_id=entry.id, value=phase_id, prefix=prefix, field="phases")
            _ensure_ref_exists(entry_id=entry.id, ref_id=phase_id, entry_ids=entry_ids, field="phase")

    if entry.kind == "sub-technique" and entry.parent is None:
        raise ValueError(
            f"Attack entry '{entry.id}' is kind='sub-technique' but has no parent"
        )


class AttackCatalogEntry(BaseModel):
    """Portable metadata about an attack id.

    Important: do not embed copyrighted framework text here.
    Keep this to identifiers and tool-friendly metadata.
    """

    id: AttackId = Field(..., description="Canonical unique attack id present in this catalog.")
    kind: AttackKind = Field(
        ..., description="Required normalized entry kind for engines and tools."
    )
    title: Optional[str] = Field(None, description="Optional short human-readable title for the attack entry.")
    url: Optional[str] = Field(None, description="Optional URL for additional reference material.")
    parent: Optional[AttackId] = Field(
        None,
        description=(
            "Optional parent attack id (same catalog namespace). Useful for hierarchical frameworks "
            "(e.g. ATT&CK technique -> sub-technique, NIST CSF function -> category -> subcategory)."
        ),
    )
    phases: Optional[List[AttackId]] = Field(
        None,
        description=(
            "Optional list of phase-like ids (same catalog namespace) that this entry is associated with. "
            "For ATT&CK, this can point to tactic ids. For kill chains, phases are typically represented as entries themselves."
        ),
    )
    tags: Optional[List[str]] = Field(
        None,
        description=(
            "Optional extra tags for grouping/filtering. Tags are non-semantic and must not replace 'kind'."
        ),
    )


class AttackCatalog(BaseModel):
    id: str = Field(
        ...,
        description=(
            "Catalog identifier and namespace for all attack ids in this catalog. "
            "All catalog.attacks[*].id values must begin with '<catalog.id>:' (e.g. catalog.id='attck' -> 'attck:T1566')."
        ),
        min_length=1,
        max_length=32,
        pattern=r"^[a-z][a-z0-9_-]{0,31}$",
    )
    framework: str = Field(
        ..., description="Free-form framework label for humans/tools. Example: 'MITRE ATT&CK Enterprise'."
    )
    attacks: List[AttackCatalogEntry] = Field(..., description="List of attack pattern catalog entries.")

    @model_validator(mode="after")
    def _validate_namespace_and_refs(self) -> "AttackCatalog":
        prefix = f"{self.id}:"
        entry_ids: Set[str] = {e.id for e in self.attacks}
        for entry in self.attacks:
            _validate_entry_refs(entry=entry, prefix=prefix, entry_ids=entry_ids)

        return self


class CRAttackCatalog(BaseModel):
    crml_attack_catalog: Literal["1.0"] = Field(
        ..., description="Attack catalog document version identifier."
    )
    meta: Meta = Field(..., description="Document metadata (name, description, tags, etc.).")
    catalog: AttackCatalog = Field(..., description="The attack catalog payload.")

    model_config = ConfigDict(populate_by_name=True)
