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
#
# Ontology dimensions intentionally answer
# different questions:
#
# owner
#     Who owns the semantic meaning?
#
# semantic_domain
#     Which scientific workflow domain
#     does it belong to?
#
# value_origin
#     Where did the value originate?
#
# projection_kind
#     How is the variable realized?
#
# analytic_kind
#     What analytical role does it play?
#
# materialization_level
#     At what operational scope does it
#     exist?
#
# node_type
#     What kind of catalog entity is it?
#
# These dimensions are intentionally
# orthogonal and should not be used as
# substitutes for one another.
#
# Examples
# --------
#
# spending.total.today
#
#     value_origin          = owl-computed
#     projection_kind       = canonical
#     analytic_kind         = primary
#     materialization_level = run
#
# spending.total.today__mean
#
#     value_origin          = roost-computed
#     projection_kind       = aggregate
#     analytic_kind         = aggregate
#
# run_execution.common_overrides
#
#     value_origin          = roost-computed
#     projection_kind       = synthetic
#     analytic_kind         = comparative
#
# =========================================================

Owner = Literal[
    "OWL",
    "ROOST",
]

# =========================================================
# Scientific Workflow Semantics
# =========================================================
#
# SemanticDomain answers:
#
#     "Which scientific workflow domain
#      does this variable belong to?"
#
# decision:
#     Retirement planning meaning,
#     policy intent, optimization goals,
#     and household decision semantics.
#
#     Examples:
#
#         spending
#         bequest
#         roth conversions
#         claiming ages
#
# design:
#     Experimental design, uncertainty
#     modeling, sampling strategy,
#     evidence generation, and study
#     methodology.
#
#     Examples:
#
#         trial counts
#         longevity assumptions
#         sweep definitions
#         scenario definitions
#
# execution:
#     Computational realization,
#     orchestration, infrastructure,
#     runtime behavior, and execution
#     diagnostics.
#
#     Examples:
#
#         elapsed_seconds
#         worker utilization
#         execution metadata
#
# These domains intentionally separate:
#
#     planning meaning
#         from
#     scientific methodology
#         from
#     computational execution
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
#
# ValueOrigin answers:
#
#     "Where did this value originate?"
#
# This dimension describes provenance,
# not analytical meaning.
#
# A value may be:
#
#     owl-computed
#
# and still be:
#
#     analytic_kind = primary
#
# because provenance and analytical role
# are intentionally separate concepts.
#
# user-specified:
#     Directly provided by the user.
#
# owl-computed:
#     Produced by OWL simulation logic.
#
# roost-computed:
#     Produced by ROOST infrastructure,
#     aggregation, comparison, synthesis,
#     formatting, or reporting logic.
#
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
# ProjectionKind answers:
#
#     "How is this variable realized?"
#
# Projection semantics describe structural
# realization rather than analytical role.
#
# Examples
# --------
#
# spending.total.today
#
#     projection_kind = canonical
#
# spending.total.today__mean
#
#     projection_kind = aggregate
#
# common_overrides
#
#     projection_kind = synthetic
#
# canonical:
#     First-class semantic variable.
#
# aggregate:
#     Projection produced through
#     aggregation of multiple rows,
#     trials, runs, or observations.
#
# composed:
#     Projection formed by combining
#     multiple semantic entities.
#
# synthetic:
#     Helper variable introduced by
#     ROOST infrastructure.
#
#     Examples:
#
#         comparison helpers
#         sweep helpers
#         preprocessing variables
#
# formatted:
#     Presentation-only projection.
#
# alias:
#     Alternate naming or shorthand
#     representation of another entity.
#
# =========================================================

ProjectionKind = Literal[
    "canonical",
    "aggregate",
    "synthetic",
]

# =========================================================
# Analytical Interpretation Semantics
# =========================================================
#
# AnalyticKind answers:
#
#     "What analytical role does this
#      variable play?"
#
# This dimension is intentionally
# independent from:
#
#     value_origin
#
#         Where the value originated.
#
#     projection_kind
#
#         How the value is realized.
#
# Examples
# --------
#
# spending.total.today
#
#     projection_kind = canonical
#     analytic_kind   = primary
#
# spending.total.today__mean
#
#     projection_kind = aggregate
#     analytic_kind   = aggregate
#
# run_execution.common_overrides
#
#     projection_kind = synthetic
#     analytic_kind   = comparative
#
# primary:
#     First-class semantic variable.
#
#     Represents a canonical modeled
#     quantity, user decision, or
#     execution metric that participates
#     directly in planning, simulation,
#     reporting, or analysis.
#
#     Examples:
#
#         spending
#         bequest
#         taxes
#         net_worth
#         success_probability
#         elapsed_seconds
#
# comparative:
#     Value exists primarily to compare
#     runs, scenarios, policies,
#     experiments, or outcomes.
#
#     Examples:
#
#         common_overrides
#         run_specific_overrides
#         diff metrics
#
# aggregate:
#     Statistical reduction across a
#     population, trial set, experiment,
#     or distribution.
#
#     Examples:
#
#         mean
#         median
#         min
#         max
#
# distributional:
#     Characterizes the shape or behavior
#     of a distribution rather than a
#     single reduced value.
#
#     Examples:
#
#         p10
#         p90
#         standard deviation
#         confidence interval
#
# inferential:
#     Derived through statistical or
#     probabilistic inference rather than
#     direct simulation output.
#
#     Examples:
#
#         regression coefficients
#         predictive estimates
#         posterior estimates
#
# =========================================================

AnalyticKind = Literal[
    "primary",
    "comparative",
    "aggregate",
]

# =========================================================
# Runtime Operational Granularity
# =========================================================
#
# MaterializationLevel answers:
#
#     "At what operational scope does
#      this value exist?"
#
# case:
#     Exists once per household case.
#
# session:
#     Exists once per ROOST session.
#
# run:
#     Exists once per simulation run.
#
# trial:
#     Exists once per stochastic trial.
#
# catalog:
#     Exists only within catalog
#     infrastructure.
#
# display:
#     Exists only within presentation
#     infrastructure.
#
# row:
#     Exists only within rendered
#     tabular representations.
#
# =========================================================

MaterializationLevel = Literal[
    "case",
    "session",
    "run",
    "trial",
    "catalog",
    "row",
]

# =========================================================
# Catalog Graph Structure
# =========================================================
#
# CatalogNodeType answers:
#
#     "What kind of catalog entity is
#      this?"
#
# VARIABLE:
#     Semantic entity tracked by the
#     catalog.
#
#     Examples:
#
#         spending
#         bequest
#         elapsed_seconds
#         spending__mean
#         ss_age_pair
#
# OVERLAY:
#     Presentation-oriented layer
#     attached to a semantic entity.
#
#     Examples:
#
#         display.net_worth
#         display.fixed_income
#
# Notes
# -----
#
# Node type describes graph structure.
#
# Projection kind describes semantic
# realization.
#
# Analytic kind describes analytical
# interpretation.
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
    Describes how an entity participates
    in the catalog graph.

    This classification is orthogonal
    to projection semantics and
    analytical interpretation.

    Examples
    --------

    spending
        VARIABLE

    display.net_worth
        OVERLAY
    """

    VARIABLE = "variable"

    OVERLAY = "overlay"


# =========================================================
# Ontology Dimension Registry
# =========================================================
#
# This registry provides the canonical
# machine-readable description of every
# ontology dimension used throughout
# ROOST.
#
# The registry exists so that:
#
#     - audits
#     - catalog views
#     - dashboards
#     - explainability systems
#     - filtering systems
#     - documentation generators
#
# can all share a single definition of
# ontology semantics.
#
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

        - ontology field name
        - display label
        - CLI alias
        - allowed values
        - semantic meaning

    Examples
    --------

    owner
        Who owns the semantic meaning?

    value_origin
        Where did the value originate?

    projection_kind
        How is the variable realized?

    analytic_kind
        What analytical role does it play?
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
            "Semantic ownership. Identifies whether semantic meaning is defined by OWL or ROOST."
        ),
    ),
    OntologyDimension(
        field_name="semantic_domain",
        label="Domain",
        cli_name="domain",
        values_type=SemanticDomain,
        description=(
            "Scientific workflow domain. "
            "Distinguishes retirement "
            "decision semantics, "
            "experimental design "
            "semantics, and execution "
            "semantics."
        ),
    ),
    OntologyDimension(
        field_name="value_origin",
        label="Origin",
        cli_name="origin",
        values_type=ValueOrigin,
        description=(
            "Value provenance. "
            "Identifies whether a value "
            "originated from user input, "
            "OWL computation, or ROOST "
            "infrastructure."
        ),
    ),
    OntologyDimension(
        field_name="projection_kind",
        label="Projection",
        cli_name="projection",
        values_type=ProjectionKind,
        description=(
            "Structural realization "
            "semantics. Describes how a "
            "variable is represented "
            "within the catalog."
        ),
    ),
    OntologyDimension(
        field_name="analytic_kind",
        label="Analytic",
        cli_name="analytic",
        values_type=AnalyticKind,
        description=(
            "Analytical role semantics. "
            "Describes how a variable "
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
            "Operational scope. Identifies the level at which a value exists within ROOST."
        ),
    ),
    OntologyDimension(
        field_name="node_type",
        label="Type",
        cli_name="type",
        values_type=CatalogNodeType,
        description=(
            "Catalog graph role. Describes how an entity participates in the catalog graph."
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

    Notes
    -----
    OntologySpec defines the canonical
    semantic classification of an entity.

    These dimensions answer different
    questions:

        owner
            Who owns the meaning?

        semantic_domain
            Which scientific workflow
            domain does it belong to?

        value_origin
            Where did the value originate?

        projection_kind
            How is the variable realized?

        analytic_kind
            What analytical role does it
            play?

        materialization_level
            At what operational scope
            does it exist?

        node_type
            What kind of catalog entity
            is it?

    Ontology metadata is intentionally
    independent from:

        - runtime execution
        - filesystem provenance
        - rendering
        - serialization
        - storage
        - implementation details

    Shared across:

        - schema fields
        - metric fields
        - aggregate metrics
        - synthetic variables
        - catalog entities
        - display overlays

    Notes
    -----
    Ontology captures:

        - classification
        - semantic meaning
        - semantic relationships

    It does NOT capture:

        - runtime history
        - execution provenance
        - audit trails
        - execution events
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
    # Value Provenance
    # =====================================================

    value_origin: ValueOrigin | None = None

    # =====================================================
    # Structural Realization
    # =====================================================

    projection_kind: ProjectionKind | None = "canonical"

    # =====================================================
    # Analytical Interpretation
    # =====================================================

    analytic_kind: AnalyticKind | None = "primary"

    # =====================================================
    # Operational Scope
    # =====================================================

    materialization_level: MaterializationLevel | None = None

    # =====================================================
    # Catalog Graph Structure
    # =====================================================

    node_type: CatalogNodeType | None = None

    # =====================================================
    # Computational Relationships
    # =====================================================
    #
    # Documents semantic variables used
    # to compute this variable.
    #
    # Example:
    #
    #     net_worth
    #
    #         <- total_assets
    #         <- total_liabilities
    #
    # =====================================================

    derived_from: list[str] = field(
        default_factory=list,
    )

    # =====================================================
    # Semantic Transformation
    # =====================================================
    #
    # Documents semantic realization
    # relationships.
    #
    # Examples:
    #
    #     ss_age_pair
    #
    #         ->
    #         fixed_income
    #             .social_security_ages
    #
    # These relationships are often used
    # by synthetic helper variables that
    # exist solely to bridge user-facing
    # configuration and canonical model
    # inputs.
    #
    # =====================================================

    materializes_to: list[str] = field(
        default_factory=list,
    )
