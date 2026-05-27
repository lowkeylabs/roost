# src/owlroost/metrics/aggregation/__init__.py

"""
Aggregation subsystem.

Responsibilities
----------------
    - aggregate metric computation
    - aggregation registry
    - aggregation execution
    - aggregate projection ontology
    - aggregate naming conventions

This subsystem intentionally does NOT own:
    - renderer overlays
    - display synthesis
    - views
    - formatting
    - rendering

Display-layer aggregate overlays are
synthesized downstream by the display
subsystem.
"""

from .aggregate_metrics import (
    build_aggregate_field_name,
    iter_aggregate_projections,
    normalize_aggregate_definition,
)

from .context import (
    AggregationContext,
)

from .registry import (
    AGG_DEFAULT_FMT,
    AGG_EXPLAINS,
    AGG_FUNCS,
    get_aggregation_explain,
    get_aggregation_func,
    list_aggregations,
)

from .service import (
    aggregate_dataset,
    aggregate_rows,
)

__all__ = [
    # =====================================================
    # Context
    # =====================================================

    "AggregationContext",

    # =====================================================
    # Registry
    # =====================================================

    "AGG_FUNCS",
    "AGG_EXPLAINS",
    "AGG_DEFAULT_FMT",
    "get_aggregation_func",
    "get_aggregation_explain",
    "list_aggregations",

    # =====================================================
    # Services
    # =====================================================

    "aggregate_rows",
    "aggregate_dataset",

    # =====================================================
    # Aggregate Projection Ontology
    # =====================================================

    "build_aggregate_field_name",
    "normalize_aggregate_definition",
    "iter_aggregate_projections",
]
