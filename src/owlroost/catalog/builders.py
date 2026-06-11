# src/owlroost/catalog/builders.py
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

from owlroost.catalog.ontology import (
    MaterializationLevel,
    ProjectionKind,
    ValueOrigin,
)
from owlroost.catalog.provenance import ProvenanceOperation
from owlroost.catalog.rows import (
    _export_provenance_chain,
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


def build_display_overlay_rows(
    display_registry,
):
    """
    Build presentation overlay rows.

    Notes
    -----
    These rows do not contribute
    ontology.

    They contribute:

        - display_name
        - profiles
        - formatting metadata
    """

    rows = []

    for field in display_registry.all_display_fields():
        profile_details = {}

        for (
            name,
            profile,
        ) in (field.profiles or {}).items():
            profile_details[name] = {
                "label": profile.label,
                "width": profile.width,
                "fmt": profile.fmt,
                "content_align": profile.content_align,
                "wrap": profile.wrap,
            }

        rows.append(
            {
                "field_name": field.field_name,
                "layer": "display",
                "provenance_chain": _export_provenance_chain(
                    _build_provenance(
                        stage="display",
                        operation=ProvenanceOperation.REGISTERED,
                        source=field,
                    )
                ),
                "display_name": (
                    getattr(
                        field,
                        "display_name",
                        None,
                    )
                    or field.field_name
                ),
                "profiles": sorted((field.profiles or {}).keys()),
                "_display": {
                    "display_name": getattr(
                        field,
                        "display_name",
                        None,
                    ),
                    "profile_details": profile_details,
                },
            }
        )

    return rows


def build_display_declaration_rows(
    display_registry,
):
    """
    Build display-authored semantic
    catalog entities.
    """

    rows = []

    for field in display_registry.all_display_fields():
        declaration = getattr(
            field,
            "catalog_declaration",
            None,
        )

        if declaration is None:
            continue

        spec = CatalogSpec(
            field_name=declaration.field_name,
            node_type=declaration.node_type,
            owner=declaration.owner,
            semantic_domain=(declaration.semantic_domain),
            value_origin=(declaration.value_origin),
            projection_kind=(declaration.projection_kind),
            analytic_kind=(declaration.analytic_kind),
            materialization_level=(declaration.materialization_level),
            derived_from=list(declaration.derived_from),
            materializes_to=list(declaration.materializes_to),
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
            description=(field.description or declaration.description),
            provenance_chain=(
                list(declaration.provenance_chain)
                + _build_provenance(
                    stage="display",
                    operation=(ProvenanceOperation.REGISTERED),
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
