# src/owlroost/display/bootstrap.py

from __future__ import annotations

from owlroost.display.overrides import (
    apply_display_overrides,
)
from owlroost.display.registry import (
    DisplayRegistry,
)
from owlroost.display.sync import (
    sync_display_registry,
)
from owlroost.display.views import (
    register_case_views,
)

# =========================================================
# Bootstrap
# =========================================================


def build_display_registry(
    schema_registry,
):
    """
    Construct fully initialized DisplayRegistry.

    Initialization order:

        1. schema → display sync
        2. register groups/views
        3. apply curated overrides
        4. validate registry

    The resulting registry is fully operational
    and ready for materialization.

    Current scope:
        - case-layer views
        - table-mode profiles
        - no aggregation
    """

    reg = DisplayRegistry()

    # =====================================================
    # Schema → Display Sync
    # =====================================================

    sync_display_registry(
        schema_registry,
        reg,
    )

    # =====================================================
    # Register Views / Groups
    # =====================================================

    register_case_views(reg)

    # =====================================================
    # Apply Curated Overrides
    # =====================================================

    apply_display_overrides(reg)

    # =====================================================
    # Validate
    # =====================================================

    reg.validate()

    return reg
