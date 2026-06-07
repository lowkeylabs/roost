# src/owlroost/catalog/ontology.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal

# =========================================================
# Canonical Semantic Dimensions
# =========================================================

Owner = Literal[
    "OWL",
    "ROOST",
]

# =========================================================
# Scientific Workflow Semantics
# =========================================================
#
# decision:
#     Defines retirement policy meaning,
#     optimization intent, or planning
#     strategy semantics.
#
# design:
#     Defines scientific methodology,
#     uncertainty modeling, experimental
#     structure, or evidence-generation
#     semantics.
#
# execution:
#     Defines computational realization,
#     orchestration, runtime execution,
#     or infrastructure behavior.
#
# These domains intentionally distinguish:
#
#     policy meaning
#         from
#     evidence-generation methodology
#         from
#     runtime realization mechanics
#
# =========================================================

SemanticDomain = Literal[
    "decision",
    "design",
    "execution",
]

# =========================================================
# Fundamental Value Provenance
# =========================================================

ValueOrigin = Literal[
    "user-specified",
    "owl-computed",
    "roost-computed",
]

# =========================================================
# Analytical Realization Semantics
# =========================================================
#
# canonical:
#     First-class semantic variable.
#
# aggregate:
#     Statistical reduction over
#     populations or trial distributions.
#
# composed:
#     Combination of multiple semantic
#     variables into a single projection.
#
# synthetic:
#     Analytical helper or derived
#     computation.
#
# formatted:
#     Presentation-only refinement.
#
# alias:
#     Alternate naming or shorthand
#     projection.
#
# =========================================================

ProjectionKind = Literal[
    "canonical",
    "aggregate",
    "composed",
    "synthetic",
    "formatted",
    "alias",
]

# =========================================================
# Analytical Interpretation Semantics
# =========================================================
#
# observed:
#     Direct runtime observation or
#     materialized metric.
#
# synthetic:
#     Row-local analytical synthesis.
#
# comparative:
#     Cross-row or cross-run analytical
#     comparison.
#
# distributional:
#     Distribution-aware comparison or
#     probabilistic characterization.
#
# inferential:
#     Statistical or probabilistic
#     inference.
#
# aggregate:
#     Statistical reduction over a
#     population or distribution.
#
# =========================================================

AnalyticKind = Literal[
    "observed",
    "synthetic",
    "comparative",
    "distributional",
    "inferential",
    "aggregate",
]

# =========================================================
# Runtime Operational Granularity
# =========================================================

MaterializationLevel = Literal[
    "case",
    "session",
    "run",
    "trial",
]

# =========================================================
# Catalog Graph Structure
# =========================================================
#
# VARIABLE
#     Semantic entity originating from
#     schema, metrics, aggregates,
#     synthetic variables, or catalog
#     synthesis.
#
#     Examples:
#
#         case_name
#         description
#         solver_options.bequest
#         timing.elapsed_seconds__mean
#
# NAMESPACE
#     Synthetic hierarchy node used
#     for ontology navigation.
#
#     Examples:
#
#         solver_options
#         aca_settings
#         timing
#
# OVERLAY
#     Presentation or projection layer
#     attached to a canonical entity.
#
#     Examples:
#
#         display.net_worth
#         display.fixed_income
#
# Notes
# -----
# CatalogNodeType answers:
#
#     "What kind of graph node is this?"
#
# ProjectionKind answers:
#
#     "What kind of semantic realization
#      is this?"
#
# These dimensions intentionally remain
# orthogonal.
#
# =========================================================


class CatalogNodeType(
    StrEnum,
):
    """
    Catalog graph structure.

    Notes
    -----
    Node type describes how an entity
    participates in the catalog graph.

    This classification is orthogonal
    to ProjectionKind.

    Examples
    --------

    aca_settings.slcsp_annual
        VARIABLE

    display.net_worth
        OVERLAY
    """

    VARIABLE = "variable"

    OVERLAY = "overlay"


# =========================================================
# Shared Ontology Specification
# =========================================================


@dataclass(kw_only=True)
class OntologySpec:
    """
    Shared semantic ontology metadata.

    This mixin defines the semantic,
    scientific, analytical, operational,
    and catalog-graph classification
    dimensions associated with a variable.

    The ontology intentionally remains
    independent from:

        - runtime extraction
        - filesystem provenance
        - execution lineage
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

    The ontology defines semantic
    classification metadata only.

    Provenance graphs, lineage tracing,
    runtime realization history, and
    analytical relationship mapping are
    handled separately by the catalog
    subsystem.
    """

    # =====================================================
    # Semantic Ownership
    # =====================================================

    owner: Owner | None = None

    # =====================================================
    # Scientific Workflow Domain
    # =====================================================

    semantic_domain: SemanticDomain | None = None

    # =====================================================
    # Fundamental Value Provenance
    # =====================================================

    value_origin: ValueOrigin | None = None

    # =====================================================
    # Analytical Realization Semantics
    # =====================================================

    projection_kind: ProjectionKind | None = "canonical"

    # =====================================================
    # Analytical Interpretation Semantics
    # =====================================================

    analytic_kind: AnalyticKind | None = None

    # =====================================================
    # Runtime Operational Granularity
    # =====================================================

    materialization_level: MaterializationLevel | None = None

    # =====================================================
    # Catalog Graph Structure
    # =====================================================

    node_type: CatalogNodeType | None = None

    # =====================================================
    # Semantic Relationships
    # =====================================================

    derived_from: list[str] = field(
        default_factory=list,
    )

    expands_to: list[str] = field(
        default_factory=list,
    )
