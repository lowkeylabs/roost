# src/owlroost/catalog/ontology.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# =========================================================
# Canonical Semantic Dimensions
# =========================================================

Owner = Literal[
    "OWL",
    "ROOST",
]

SemanticDomain = Literal[
    "decision",
    "design",
    "execution",
]

ValueOrigin = Literal[
    "user-specified",
    "owl-computed",
    "roost-computed",
]

ProjectionKind = Literal[
    "canonical",
    "aggregate",
    "composed",
    "synthetic",
    "formatted",
    "alias",
]

MaterializationLevel = Literal[
    "case",
    "session",
    "run",
    "trial",
]


# =========================================================
# Shared Ontology Specification
# =========================================================


@dataclass(kw_only=True)
class OntologySpec:
    """
    Shared semantic ontology metadata.

    This mixin defines the scientific,
    provenance, and analytical semantics
    associated with a variable.

    The ontology intentionally remains
    independent from:

        - runtime extraction
        - rendering/layout
        - storage implementation
        - serialization

    These ontology dimensions are shared
    across:

        - schema fields
        - metric fields
        - aggregate metrics
        - catalog variables
        - synthetic projections
        - display aliases
    """

    # =====================================================
    # Semantic Ownership
    # =====================================================

    owner: Owner | None = None

    # =====================================================
    # Scientific Workflow Domain
    # =====================================================

    semantic_domain: (
        SemanticDomain | None
    ) = None

    # =====================================================
    # Fundamental Value Provenance
    # =====================================================

    value_origin: (
        ValueOrigin | None
    ) = None

    # =====================================================
    # Projection Semantics
    # =====================================================

    projection_kind: (
        ProjectionKind | None
    ) = "canonical"

    # =====================================================
    # Runtime Materialization
    # =====================================================

    materialization_level: (
        MaterializationLevel | None
    ) = None
