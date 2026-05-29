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
# variable:
#     Canonical semantic entity.
#
# namespace:
#     Synthetic hierarchical grouping
#     node used for ontology navigation.
#
# overlay:
#     Projection or presentation layer
#     attached to a canonical entity.
#
# =========================================================

CatalogNodeType = Literal[
    "variable",
    "namespace",
    "overlay",
]

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

    node_type: CatalogNodeType | None = "variable"
