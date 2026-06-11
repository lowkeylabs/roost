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
from typing import Literal, get_args

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
# Ontology Dimension Registry
# =========================================================


OntologyDimensionName = Literal[
    "owner",
    "semantic_domain",
    "value_origin",
    "projection_kind",
    "analytic_kind",
    "materialization_level",
    "node_type",
]


@dataclass(frozen=True)
class OntologyDimension:
    """
    Canonical ontology dimension metadata.

    Notes
    -----
    Defines:

        - catalog field name
        - human-readable label
        - CLI/filter alias
        - allowed value type
        - semantic description

    This registry acts as the single
    source of truth for ontology
    dashboards, audits, filtering,
    explainability, and documentation.
    """

    field_name: OntologyDimensionName

    label: str

    cli_name: str

    values_type: object

    description: str

    @property
    def values(
        self,
    ) -> list[str]:
        values = get_args(
            self.values_type,
        )

        if values:
            return list(
                values,
            )

        if issubclass(
            self.values_type,
            StrEnum,
        ):
            return [value.value for value in self.values_type]

        raise TypeError(f"Unsupported ontology value type: {self.values_type}")


ONTOLOGY_DIMENSIONS = [
    OntologyDimension(
        field_name="owner",
        label="Owner",
        cli_name="owner",
        values_type=Owner,
        description=(
            "Semantic ownership of a variable. "
            "Identifies whether the variable "
            "originates from OWL or ROOST."
        ),
    ),
    OntologyDimension(
        field_name="semantic_domain",
        label="Domain",
        cli_name="domain",
        values_type=SemanticDomain,
        description=(
            "Scientific workflow domain. "
            "Distinguishes retirement policy "
            "semantics from methodology and "
            "runtime execution concerns."
        ),
    ),
    OntologyDimension(
        field_name="value_origin",
        label="Origin",
        cli_name="origin",
        values_type=ValueOrigin,
        description=(
            "Fundamental value provenance. "
            "Identifies whether a value is "
            "user-specified, OWL-computed, "
            "or ROOST-computed."
        ),
    ),
    OntologyDimension(
        field_name="projection_kind",
        label="Projection",
        cli_name="projection",
        values_type=ProjectionKind,
        description=(
            "Analytical realization semantics. "
            "Describes how a variable is "
            "projected from underlying "
            "semantic entities."
        ),
    ),
    OntologyDimension(
        field_name="analytic_kind",
        label="Analytic",
        cli_name="analytic",
        values_type=AnalyticKind,
        description=(
            "Analytical interpretation "
            "semantics. Describes how a value "
            "should be interpreted during "
            "analysis."
        ),
    ),
    OntologyDimension(
        field_name="materialization_level",
        label="Level",
        cli_name="level",
        values_type=MaterializationLevel,
        description=(
            "Runtime operational granularity. "
            "Identifies whether a value exists "
            "at the case, session, run, or "
            "trial level."
        ),
    ),
    OntologyDimension(
        field_name="node_type",
        label="Type",
        cli_name="type",
        values_type=CatalogNodeType,
        description=(
            "Catalog graph structure. Describes how an entity participates in the catalog graph."
        ),
    ),
]

_ONTOLOGY_DIMENSIONS = {d.field_name: d for d in ONTOLOGY_DIMENSIONS}


def get_ontology_dimension(
    field_name,
):
    return _ONTOLOGY_DIMENSIONS.get(
        field_name,
    )


_ALIAS_MAP = {d.cli_name: d.field_name for d in ONTOLOGY_DIMENSIONS}


def normalize_ontology_field_name(
    name,
):
    return _ALIAS_MAP.get(
        name,
        name,
    )


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

    materializes_to: list[str] = field(
        default_factory=list,
    )
