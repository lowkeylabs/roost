# src/owlroost/display/bootstrap.py

from __future__ import annotations

from owlroost.display.overrides import (
    apply_display_overrides,
)
from owlroost.display.registry import (
    DisplayRegistry,
)
from owlroost.display.sync import (
    sync_metrics_registry,
    sync_schema_registry,
)
from owlroost.display.views import (
    register_case_views,
    register_run_views,
)
from owlroost.metrics.aggregation.display_fields import (
    register_aggregate_display_fields,
)

# =========================================================
# Bootstrap
# =========================================================


def build_display_registry(
    schema_registry,
    metrics_registry,
):
    """
    Construct fully initialized DisplayRegistry.

    Initialization order:

        1. input schema → display sync
        2. metrics schema → display sync
        3. aggregate display field synthesis
        4. register groups/views
        5. apply curated overrides
        6. validate registry

    The resulting registry is fully operational
    and ready for materialization.

    DisplayRegistry is intentionally renderer-facing.

    Semantic ownership belongs to:

        - schema_registry  -> input semantics
        - metrics_registry -> output semantics

    DisplayRegistry owns only presentation semantics:

        - labels
        - formatting
        - alignment
        - visibility
        - grouping
        - views
    """

    reg = DisplayRegistry()

    # =====================================================
    # Attach semantic registries
    # =====================================================

    reg.schema_registry = schema_registry
    reg.metrics_registry = metrics_registry

    # =====================================================
    # Input Schema → Display Sync
    # =====================================================

    sync_schema_registry(
        schema_registry,
        reg,
    )

    # =====================================================
    # Metrics Schema → Display Sync
    # =====================================================

    sync_metrics_registry(
        metrics_registry,
        reg,
    )

    # =====================================================
    # Aggregate Display Fields
    # =====================================================

    register_aggregate_display_fields(
        reg,
        metrics_registry,
    )

    # =====================================================
    # Register Views / Groups
    # =====================================================

    register_case_views(
        reg,
    )

    register_run_views(
        reg,
    )

    # =====================================================
    # Apply Curated Overrides
    # =====================================================

    apply_display_overrides(
        reg,
    )

    # =====================================================
    # Validate
    # =====================================================

    reg.validate()

    return reg
