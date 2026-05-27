# src/owlroost/catalog/builders.py

from __future__ import annotations

from owlroost.catalog.rows import (
    build_catalog_row,
)

from owlroost.catalog.specs import (
    CatalogSpec,
    ProvenanceEvent,
)

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
    operation: str,
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
            # -------------------------------------------------
            # Ontology
            # -------------------------------------------------
            owner=field.owner,
            semantic_domain=(
                field.semantic_domain
            ),
            value_origin=(
                field.value_origin
                or "user-specified"
            ),
            projection_kind=(
                field.projection_kind
                or "canonical"
            ),
            materialization_level=(
                field.materialization_level
                or "run"
            ),
            node_type=(
                field.node_type
            ),
            # -------------------------------------------------
            # Runtime Realization
            # -------------------------------------------------
            source="_inputs",
            path=_normalize_path(
                field.path
            ),
            # -------------------------------------------------
            # Explainability
            # -------------------------------------------------
            description=(
                field.description
            ),
            # -------------------------------------------------
            # Lineage
            # -------------------------------------------------
            derived_from=(
                list(
                    field.derived_from
                )
            ),
            # -------------------------------------------------
            # Provenance
            # -------------------------------------------------
            provenance_chain=(
                _build_provenance(
                    stage="schema",
                    operation="REGISTERED",
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
            # -------------------------------------------------
            # Ontology
            # -------------------------------------------------
            owner=metric.owner,
            semantic_domain=(
                metric.semantic_domain
            ),
            value_origin=(
                metric.value_origin
                or "owl-computed"
            ),
            projection_kind=(
                metric.projection_kind
                or "canonical"
            ),
            materialization_level=(
                metric.materialization_level
                or "trial"
            ),
            node_type=(
                metric.node_type
            ),
            # -------------------------------------------------
            # Runtime Realization
            # -------------------------------------------------
            source="_metrics",
            path=metric.name,
            # -------------------------------------------------
            # Explainability
            # -------------------------------------------------
            description=(
                metric.description
            ),
            # -------------------------------------------------
            # Lineage
            # -------------------------------------------------
            derived_from=(
                list(
                    metric.derived_from
                )
            ),
            # -------------------------------------------------
            # Provenance
            # -------------------------------------------------
            provenance_chain=(
                _build_provenance(
                    stage="metrics",
                    operation="REGISTERED",
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
    Infer runtime source realization
    for display overlays.
    """

    if field.display_fn is not None:
        return "display_fn"

    path = field.path or ""

    if path.startswith("_metrics"):
        return "_metrics"

    if path.startswith("_meta"):
        return "_meta"

    if path.startswith("_paths"):
        return "_paths"

    if path.startswith("_inputs"):
        return "_inputs"

    semantic_field = (
        field.semantic_field
    )

    if semantic_field is not None:

        source = getattr(
            semantic_field,
            "source",
            None,
        )

        if source == "metrics":
            return "_metrics"

        return "_inputs"

    return "display"


def infer_display_projection_kind(
    field,
):
    """
    Infer analytical projection semantics
    for display overlays.
    """

    # -----------------------------------------------------
    # Synthetic analytical projection
    # -----------------------------------------------------

    if field.display_fn is not None:
        return "synthetic"

    # -----------------------------------------------------
    # Multi-field composition
    # -----------------------------------------------------

    if field.field_name.startswith(
        "compact_"
    ):
        return "composed"

    # -----------------------------------------------------
    # Presentation refinement
    # -----------------------------------------------------

    return "formatted"


def build_display_rows(
    display_registry,
):
    """
    Build catalog overlay rows from
    display registry.

    Notes
    -----
    Display fields no longer define
    canonical semantic ontology.

    Instead they represent:

        projection overlays

    layered on top of existing semantic
    entities originating from:

        - schema ontology
        - metrics ontology
        - runtime metadata
    """

    rows = []

    for field in (
        display_registry.all_display_fields()
    ):

        semantic_field = (
            field.semantic_field
        )

        owner = None

        semantic_domain = None

        value_origin = (
            "roost-computed"
        )

        materialization_level = (
            "run"
        )

        node_type = "variable"

        # -------------------------------------------------
        # Semantic inheritance
        # -------------------------------------------------

        if semantic_field is not None:

            owner = getattr(
                semantic_field,
                "owner",
                None,
            )

            semantic_domain = getattr(
                semantic_field,
                "semantic_domain",
                None,
            )

            value_origin = getattr(
                semantic_field,
                "value_origin",
                value_origin,
            )

            materialization_level = getattr(
                semantic_field,
                "materialization_level",
                materialization_level,
            )

            node_type = getattr(
                semantic_field,
                "node_type",
                node_type,
            )

        spec = CatalogSpec(
            # -------------------------------------------------
            # Canonical Identity
            # -------------------------------------------------
            field_name=field.field_name,
            # -------------------------------------------------
            # Ontology
            # -------------------------------------------------
            owner=owner,
            semantic_domain=(
                semantic_domain
            ),
            value_origin=(
                value_origin
            ),
            projection_kind=(
                infer_display_projection_kind(
                    field
                )
            ),
            materialization_level=(
                materialization_level
            ),
            node_type=node_type,
            # -------------------------------------------------
            # Runtime Realization
            # -------------------------------------------------
            source=infer_display_source(
                field
            ),
            path=field.path,
            # -------------------------------------------------
            # Explainability
            # -------------------------------------------------
            description=(
                field.description
            ),
            # -------------------------------------------------
            # Provenance
            # -------------------------------------------------
            provenance_chain=(
                _build_provenance(
                    stage="display",
                    operation="OVERLAYED",
                    source=field,
                )
            ),
        )

        rows.append(
            build_catalog_row(
                spec=spec,
                layer="display",
                semantic_field=(
                    semantic_field
                ),
                display_field=field,
            )
        )

    return rows
