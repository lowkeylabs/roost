# src/owlroost/display/bootstrap.py

from __future__ import annotations

from owlroost.display.fields import (
    register_all_display_fields,
)
from owlroost.display.groups import (
    register_display_groups,
)
from owlroost.display.registry import (
    DisplayRegistry,
)
from owlroost.display.sync import (
    sync_metrics_registry,
    sync_schema_registry,
)
from owlroost.display.views import (
    register_display_views,
)
from owlroost.metrics.aggregation.aggregate_metrics import (
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
        4. register display fields
        5. register display groups
        6. register display views
        7. validate registry


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
    # Register Display Fields
    # =====================================================

    register_all_display_fields(
        reg,
    )

    # =====================================================
    # Register Display Groups
    # =====================================================

    register_display_groups(
        reg,
    )

    # =====================================================
    # Register Display Views
    # =====================================================

    register_display_views(
        reg,
    )

    # =====================================================
    # Validate
    # =====================================================

    reg.validate()

    return reg
