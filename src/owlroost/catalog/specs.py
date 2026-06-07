# src/owlroost/catalog/specs.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
Catalog semantic specifications.

Notes
-----
CatalogSpec represents the canonical
semantic identity tracked by the ROOST
catalog subsystem.

The catalog acts as the semantic
integration layer across:

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
"""

from __future__ import annotations

from dataclasses import (
    dataclass,
    field,
)

from owlroost.catalog.ontology import (
    OntologySpec,
)
from owlroost.catalog.provenance import (
    ProvenanceEvent,
    defined_in,
    origin_file,
    provenance_depth,
    provenance_summary,
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
    CatalogSpec represents a semantic
    entity rather than a flattened
    registry row.

    Architectural Invariant
    -----------------------
    ROOST maintains:

        one canonical semantic identity
        per variable

    CatalogSpec therefore accumulates
    semantic enrichment from multiple
    registries while preserving a single
    canonical ontology node.
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
    # Provenance Evolution
    #
    # Invariant:
    #
    #     oldest -> newest
    #
    # First event:
    #
    #     semantic origin
    #
    # Last event:
    #
    #     most recent modification
    # =====================================================

    provenance_chain: list[ProvenanceEvent] = field(
        default_factory=list,
    )

    # =====================================================
    # Derived Provenance
    # =====================================================

    @property
    def origin_file(
        self,
    ) -> str | None:
        """
        File where this semantic entity
        first entered the catalog.
        """

        return origin_file(
            self.provenance_chain,
        )

    @property
    def defined_in(
        self,
    ) -> str | None:
        """
        File associated with the most
        recent semantic modification.
        """

        return defined_in(
            self.provenance_chain,
        )

    @property
    def provenance_depth(
        self,
    ) -> int:
        """
        Number of provenance events.
        """

        return provenance_depth(
            self.provenance_chain,
        )

    @property
    def provenance_summary(
        self,
    ) -> str:
        """
        Compact provenance rendering.
        """

        return provenance_summary(
            self.provenance_chain,
        )

    # =====================================================
    # Provenance Mutation
    # =====================================================

    def add_provenance(
        self,
        *,
        stage: str,
        operation: str,
        file: str,
        detail: dict | None = None,
    ):
        """
        Append provenance event.

        Events are appended in temporal
        order and therefore preserve the
        oldest -> newest invariant.
        """

        self.provenance_chain.append(
            ProvenanceEvent(
                stage=stage,
                operation=operation,
                file=file,
                detail=detail or {},
            )
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
