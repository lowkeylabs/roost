# src/owlroost/catalog/builders.py

from __future__ import annotations

from .rows import build_catalog_row

# =========================================================
# Schema Registry
# =========================================================


def build_schema_rows(
    schema_registry,
):
    """
    Build catalog rows from schema registry.

    Schema fields represent executable ontology
    and typically materialize into:

        _inputs
    """

    rows = []

    for field in schema_registry.all():
        rows.append(
            build_catalog_row(
                field_name=field.name,
                layer="schema",
                source="_inputs",
                path=".".join(field.path)
                if isinstance(
                    field.path,
                    tuple,
                )
                else field.path,
                description=field.description,
                semantic_owner="schema",
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
    Build catalog rows from metrics registry.

    Metrics fields represent observable runtime
    ontology and typically materialize into:

        _metrics
    """

    rows = []

    for metric in metrics_registry.all():
        rows.append(
            build_catalog_row(
                field_name=metric.name,
                layer="metrics",
                source="_metrics",
                path=metric.name,
                description=metric.description,
                semantic_owner="metrics",
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
    Infer runtime source domain for DisplayField.

    Notes
    -----
    Display fields may project values from:

        - _inputs
        - _metrics
        - _meta
        - _paths
        - display_fn synthesized values

    This is intentionally heuristic for now.
    """

    # -----------------------------------------------------
    # Synthesized display function
    # -----------------------------------------------------

    if field.display_fn is not None:
        return "display_fn"

    path = field.path or ""

    # -----------------------------------------------------
    # Explicit runtime domains
    # -----------------------------------------------------

    if path.startswith("_metrics"):
        return "_metrics"

    if path.startswith("_meta"):
        return "_meta"

    if path.startswith("_paths"):
        return "_paths"

    if path.startswith("_inputs"):
        return "_inputs"

    # -----------------------------------------------------
    # Semantic bridge
    # -----------------------------------------------------

    semantic_field = field.semantic_field

    if semantic_field is not None:
        source = getattr(
            semantic_field,
            "source",
            None,
        )

        if source == "metrics":
            return "_metrics"

        return "_inputs"

    # -----------------------------------------------------
    # Default
    # -----------------------------------------------------

    return "display"


def build_display_rows(
    display_registry,
):
    """
    Build catalog rows from display registry.

    Display fields represent analytical projection
    ontology layered on top of canonical semantic
    registries.
    """

    rows = []

    for field in display_registry.all_display_fields():
        semantic_owner = None

        if field.semantic_field is not None:
            semantic_owner = getattr(
                field.semantic_field,
                "source",
                None,
            )

        rows.append(
            build_catalog_row(
                field_name=field.field_name,
                layer="display",
                source=infer_display_source(field),
                path=field.path,
                description=field.description,
                semantic_owner=semantic_owner,
                semantic_field=field.semantic_field,
                display_field=field,
            )
        )

    return rows
