# src/owlroost/catalog/builders.py

from __future__ import annotations

from owlroost.catalog.ontology import (
    AnalyticKind,
    MaterializationLevel,
    ProjectionKind,
    SemanticDomain,
    ValueOrigin,
)
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

DEFAULT_DISPLAY_VALUE_ORIGIN: ValueOrigin = "roost-computed"

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

    return "display"


def infer_display_projection_kind(
    field,
) -> ProjectionKind:
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

    if field.field_name.startswith("compact_"):
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

    for field in display_registry.all_display_fields():
        semantic_field = field.semantic_field

        owner = None

        semantic_domain: SemanticDomain | None = None

        analytic_kind: AnalyticKind | None = None

        value_origin: ValueOrigin = DEFAULT_DISPLAY_VALUE_ORIGIN

        materialization_level: MaterializationLevel = DEFAULT_RUN_LEVEL

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

            analytic_kind = getattr(
                semantic_field,
                "analytic_kind",
                None,
            )

            value_origin = (
                getattr(
                    semantic_field,
                    "value_origin",
                    None,
                )
                or value_origin
            )

            materialization_level = (
                getattr(
                    semantic_field,
                    "materialization_level",
                    None,
                )
                or materialization_level
            )

        spec = CatalogSpec(
            # -------------------------------------------------
            # Canonical Identity
            # -------------------------------------------------
            field_name=field.field_name,
            node_type="variable",
            # -------------------------------------------------
            # Ontology
            # -------------------------------------------------
            owner=owner,
            semantic_domain=(semantic_domain),
            value_origin=(value_origin),
            projection_kind=(infer_display_projection_kind(field)),
            analytic_kind=(analytic_kind),
            materialization_level=(materialization_level),
            # -------------------------------------------------
            # Runtime Realization
            # -------------------------------------------------
            source=infer_display_source(field),
            path=field.path,
            # -------------------------------------------------
            # Explainability
            # -------------------------------------------------
            description=(field.description),
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
                semantic_field=(semantic_field),
                display_field=field,
            )
        )

    return rows
