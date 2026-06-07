# src/owlroost/catalog/builders.py
#
# Copyright (c) 2026 John Leonard
# All rights reserved.
# SPDX-License-Identifier: LicenseRef-OwlRoost-Proprietary
# See LICENSE file in repository root.

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from owlroost.catalog.ontology import (
    MaterializationLevel,
    ProjectionKind,
    ValueOrigin,
)
from owlroost.catalog.provenance import ProvenanceOperation
from owlroost.catalog.rows import (
    build_catalog_row,
)
from owlroost.catalog.specs import (
    CatalogSpec,
    ProvenanceEvent,
)

# =========================================================
# Typed Defaults
# =========================================================

DEFAULT_SCHEMA_VALUE_ORIGIN: ValueOrigin = "user-specified"

DEFAULT_METRIC_VALUE_ORIGIN: ValueOrigin = "owl-computed"

DEFAULT_CANONICAL_PROJECTION: ProjectionKind = "canonical"

DEFAULT_RUN_LEVEL: MaterializationLevel = "run"

DEFAULT_TRIAL_LEVEL: MaterializationLevel = "trial"

# =========================================================
# Helpers
# =========================================================


def _normalize_path(
    path,
):
    """
    Normalize runtime paths into stable
    dotted-string representations.
    """

    if path is None:
        return None

    if isinstance(
        path,
        tuple,
    ):
        return ".".join(path)

    return str(path)


def _build_provenance(
    *,
    stage: str,
    operation: ProvenanceOperation,
    source,
):
    """
    Construct lightweight provenance chain.
    """

    return [
        ProvenanceEvent(
            stage=stage,
            operation=operation,
            file=(
                getattr(
                    source,
                    "defined_in",
                    None,
                )
                or stage
            ),
        )
    ]


# =========================================================
# Schema Registry
# =========================================================


def build_schema_rows(
    schema_registry,
):
    """
    Build canonical catalog rows from
    executable schema ontology.

    Notes
    -----
    Schema fields primarily represent:

        - executable user ontology
        - canonical semantic variables
        - analytical input definitions
    """

    rows = []

    for field in schema_registry.all():
        spec = CatalogSpec(
            # -------------------------------------------------
            # Canonical Identity
            # -------------------------------------------------
            field_name=field.name,
            node_type="variable",
            # -------------------------------------------------
            # Ontology
            # -------------------------------------------------
            owner=field.owner,
            semantic_domain=(field.semantic_domain),
            value_origin=(field.value_origin or DEFAULT_SCHEMA_VALUE_ORIGIN),
            projection_kind=(field.projection_kind or DEFAULT_CANONICAL_PROJECTION),
            analytic_kind=getattr(
                field,
                "analytic_kind",
                None,
            ),
            materialization_level=(field.materialization_level or DEFAULT_RUN_LEVEL),
            # -------------------------------------------------
            # Runtime Realization
            # -------------------------------------------------
            source="_inputs",
            path=_normalize_path(field.path),
            # -------------------------------------------------
            # Explainability
            # -------------------------------------------------
            description=(field.description),
            # -------------------------------------------------
            # Analytical Lineage
            # -------------------------------------------------
            derived_from=list(
                getattr(
                    field,
                    "derived_from",
                    [],
                )
            ),
            # -------------------------------------------------
            # Provenance
            # -------------------------------------------------
            provenance_chain=(
                _build_provenance(
                    stage="schema",
                    operation=ProvenanceOperation.REGISTERED,
                    source=field,
                )
            ),
        )

        rows.append(
            build_catalog_row(
                spec=spec,
                layer="schema",
                semantic_field=field,
            )
        )

    return rows


# =========================================================
# Metrics Registry
# =========================================================


def build_metric_rows(
    metrics_registry,
):
    """
    Build canonical catalog rows from
    observable metrics ontology.

    Notes
    -----
    Metrics represent runtime-observable
    ontology generated through:

        - OWL execution
        - ROOST orchestration
        - aggregation synthesis
        - analytical projections
    """

    rows = []

    for metric in metrics_registry.all():
        spec = CatalogSpec(
            # -------------------------------------------------
            # Canonical Identity
            # -------------------------------------------------
            field_name=metric.name,
            node_type="variable",
            # -------------------------------------------------
            # Ontology
            # -------------------------------------------------
            owner=metric.owner,
            semantic_domain=(metric.semantic_domain),
            value_origin=(metric.value_origin or DEFAULT_METRIC_VALUE_ORIGIN),
            projection_kind=(metric.projection_kind or DEFAULT_CANONICAL_PROJECTION),
            analytic_kind=getattr(
                metric,
                "analytic_kind",
                None,
            ),
            materialization_level=(metric.materialization_level or DEFAULT_TRIAL_LEVEL),
            # -------------------------------------------------
            # Runtime Realization
            # -------------------------------------------------
            source="_metrics",
            path=metric.name,
            # -------------------------------------------------
            # Explainability
            # -------------------------------------------------
            description=(metric.description),
            # -------------------------------------------------
            # Analytical Lineage
            # -------------------------------------------------
            derived_from=list(
                getattr(
                    metric,
                    "derived_from",
                    [],
                )
            ),
            # -------------------------------------------------
            # Provenance
            # -------------------------------------------------
            provenance_chain=(
                _build_provenance(
                    stage="metrics",
                    operation=ProvenanceOperation.REGISTERED,
                    source=metric,
                )
            ),
        )

        rows.append(
            build_catalog_row(
                spec=spec,
                layer="metrics",
                semantic_field=metric,
            )
        )

    return rows


# =========================================================
# Display Registry
# =========================================================


def infer_display_source(
    field,
):
    """
    Infer runtime realization source for a
    display-authored catalog declaration.
    """

    path = (
        getattr(
            field,
            "path",
            None,
        )
        or ""
    )

    if path.startswith("_metrics"):
        return "_metrics"

    if path.startswith("_meta"):
        return "_meta"

    if path.startswith("_paths"):
        return "_paths"

    if path.startswith("_inputs"):
        return "_inputs"

    return "display"


def build_display_rows(
    display_registry,
):
    """
    Build catalog rows from display-authored
    catalog declarations.

    Notes
    -----
    Model B3 Architecture
    ---------------------

    Display owns presentation metadata.

    Catalog owns semantic identity.

    Display modules may optionally author
    semantic declarations through:

        DisplayField.field(...)

    Those declarations are represented as
    CatalogSpec instances attached to the
    DisplayField and participate in catalog
    synthesis.

    Presentation-only overlays do not
    contribute semantic rows.
    """

    rows = []

    for field in display_registry.all_display_fields():
        declaration = getattr(
            field,
            "catalog_declaration",
            None,
        )

        # -------------------------------------------------
        # Presentation Overlay
        # -------------------------------------------------

        if declaration is None:
            continue

        # -------------------------------------------------
        # Display-Authored Semantic Declaration
        # -------------------------------------------------

        spec = CatalogSpec(
            # =============================================
            # Canonical Identity
            # =============================================
            field_name=declaration.field_name,
            node_type=declaration.node_type,
            # =============================================
            # Ontology
            # =============================================
            owner=declaration.owner,
            semantic_domain=(declaration.semantic_domain),
            value_origin=(declaration.value_origin),
            projection_kind=(declaration.projection_kind),
            analytic_kind=(declaration.analytic_kind),
            materialization_level=(declaration.materialization_level),
            derived_from=list(declaration.derived_from),
            expands_to=list(declaration.expands_to),
            # =============================================
            # Runtime Realization
            # =============================================
            source=(
                infer_display_source(
                    field,
                )
            ),
            path=getattr(
                field,
                "path",
                None,
            ),
            # =============================================
            # Explainability
            # =============================================
            description=(field.description or declaration.description),
            # =============================================
            # Provenance
            # =============================================
            provenance_chain=(
                list(declaration.provenance_chain)
                + _build_provenance(
                    stage="display",
                    operation=ProvenanceOperation.REGISTERED,
                    source=field,
                )
            ),
        )

        rows.append(
            build_catalog_row(
                spec=spec,
                layer="display",
                display_field=field,
            )
        )

    return rows
