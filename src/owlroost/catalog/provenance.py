# src/owlroost/catalog/provenance.py

"""
Catalog provenance infrastructure.

Notes
-----
Provenance records semantic evolution of a
catalog variable across the ROOST pipeline.

Architectural Invariant
-----------------------

provenance_chain is ordered:

    oldest -> newest

The first event represents semantic origin.

The final event represents the most recent
semantic modification.

CatalogSpec owns provenance chains.

This module defines provenance structures
and helper utilities only.
"""

from __future__ import annotations

from dataclasses import (
    dataclass,
    field,
)
from enum import StrEnum
from typing import Any

# =========================================================
# Provenance Operations
# =========================================================


class ProvenanceOperation(
    StrEnum,
):
    """
    Canonical provenance operations.
    """

    REGISTERED = "registered"

    OVERLAY = "overlay"

    COMPOSED = "composed"

    AGGREGATE_DERIVED = "aggregate_derived"

    FORMATTED = "formatted"

    MATERIALIZED = "materialized"

    ALIAS_CREATED = "alias_created"


# =========================================================
# Provenance Event
# =========================================================


@dataclass(slots=True)
class ProvenanceEvent:
    """
    Record semantic evolution of a variable.

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

    operation: ProvenanceOperation

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
# Helpers
# =========================================================


def origin_file(
    provenance_chain: list[ProvenanceEvent],
) -> str | None:
    """
    Return file where variable first entered
    the semantic pipeline.
    """

    for event in provenance_chain:
        if event.file:
            return event.file

    return None


def defined_in(
    provenance_chain: list[ProvenanceEvent],
) -> str | None:
    """
    Return file associated with the most
    recent semantic modification.
    """

    for event in reversed(
        provenance_chain,
    ):
        if event.file:
            return event.file

    return None


def provenance_depth(
    provenance_chain: list[ProvenanceEvent],
) -> int:
    """
    Return number of provenance events.
    """

    return len(
        provenance_chain,
    )


def provenance_summary(
    provenance_chain: list[ProvenanceEvent],
) -> str:
    """
    Compact human-readable provenance summary.
    """

    files = [event.file for event in provenance_chain if event.file]

    return " -> ".join(
        files,
    )
