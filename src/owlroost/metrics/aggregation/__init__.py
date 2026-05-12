# src/owlroost/metrics/aggregation/__init__.py

"""
Aggregation subsystem.

Responsibilities:
    - aggregate metric computation
    - aggregation registry
    - aggregation execution
    - aggregate display field synthesis

This subsystem intentionally does NOT own:
    - metric semantics
    - display views
    - rendering
"""

from .context import AggregationContext
from .display_fields import (
    build_aggregate_field_name,
    register_aggregate_display_fields,
)
from .registry import (
    AGG_DEFAULT_FMT,
    AGG_FUNCS,
)
from .service import (
    aggregate_dataset,
    aggregate_rows,
)

__all__ = [
    # Context
    "AggregationContext",
    # Registry
    "AGG_FUNCS",
    "AGG_DEFAULT_FMT",
    # Services
    "aggregate_rows",
    "aggregate_dataset",
    # Display helpers
    "register_aggregate_display_fields",
    "build_aggregate_field_name",
]
