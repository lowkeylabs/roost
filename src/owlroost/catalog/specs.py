# src/owlroost/catalog/specs.py

from __future__ import annotations

from dataclasses import (
    dataclass,
    field,
)
from typing import (
    Any,
)

from owlroost.catalog.ontology import (
    OntologySpec,
)

# =========================================================
# Provenance
# =========================================================


@dataclass
class ProvenanceEvent:
    """
    Record semantic evolution of a variable
    through the ROOST analytical pipeline.

    Notes
    -----
    Provenance intentionally captures:

        - ontology registration
        - aggregation derivation
        - projection overlays
        - analytical synthesis
        - formatting refinement
        - runtime materialization

    without redefining canonical semantic
    identity.
    """

    # =====================================================
    # Pipeline Stage
    # =====================================================

    stage: str

    # =====================================================
    # Operation
    # =====================================================

    operation: str

    # =====================================================
    # Source File
    # =====================================================

    file: str

    # =====================================================
    # Optional Metadata
    # =====================================================

    detail: dict[
        str,
        Any,
    ] = field(
        default_factory=dict,
    )


# =========================================================
# Catalog Specification
# =========================================================


@dataclass
class CatalogSpec(
    OntologySpec,
):
    """
    Canonical semantic catalog specification.

    Notes
    -----
    CatalogSpec represents the normalized
    semantic identity tracked by the ROOST
    catalog subsystem.

    OntologySpec intentionally acts as a
    lightweight semantic mixin defining:

        - ownership semantics
        - workflow semantics
        - analytical semantics
        - projection semantics
        - operational semantics
        - catalog graph semantics

    The catalog intentionally acts as:

        - semantic integration infrastructure
        - provenance infrastructure
        - explainability infrastructure
        - analytical navigation infrastructure

    layered across:

        - schema ontology
        - metrics ontology
        - display overlays
        - aggregation synthesis
        - runtime realization

    while preserving:

        - canonical semantic identity
        - ontology semantics
        - workflow semantics
        - projection lineage
        - provenance evolution

    Architectural Invariant
    -----------------------
    ROOST maintains:

        one canonical semantic identity
        per variable

    CatalogSpec therefore models:

        semantic entities

    rather than merely flattened
    registry rows.
    """

    # =====================================================
    # Canonical Semantic Identity
    # =====================================================

    field_name: str

    # =====================================================
    # Runtime Realization
    # =====================================================

    source: str | None = None

    path: str | None = None

    # =====================================================
    # Explainability
    # =====================================================

    description: str | None = None

    # =====================================================
    # Analytical Lineage
    # =====================================================

    derived_from: list[str] = field(
        default_factory=list,
    )

    # =====================================================
    # Provenance Evolution
    # =====================================================

    provenance_chain: list[ProvenanceEvent] = field(
        default_factory=list,
    )

    # =====================================================
    # Post Init
    # =====================================================

    def __post_init__(
        self,
    ):
        """
        Normalize lightweight metadata.
        """

        if self.path == "":
            self.path = None
