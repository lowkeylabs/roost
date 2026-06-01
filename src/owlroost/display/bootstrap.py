# src/owlroost/display/bootstrap.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

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

# =========================================================
# Bootstrap
# =========================================================


def build_display_registry(
    schema_registry,
    metrics_registry,
):
    """
    Construct fully initialized DisplayRegistry.

    Notes
    -----
    DisplayRegistry is renderer-facing overlay
    infrastructure layered atop canonical
    ontology registries.

    Canonical semantic ownership belongs to:

        - schema_registry
        - metrics_registry

    DisplayRegistry owns only presentation
    semantics:

        - labels
        - formatting
        - alignment
        - visibility
        - grouping
        - views
        - rendering overlays

    Initialization Order
    --------------------

    1. schema ontology overlays
    2. metrics ontology overlays
    3. explicit display field overlays
    4. display groups
    5. display views
    6. validation
    """

    reg = DisplayRegistry()

    # =====================================================
    # Canonical Ontology Registries
    # =====================================================

    reg.schema_registry = schema_registry

    reg.metrics_registry = metrics_registry

    # =====================================================
    # Schema Display Overlays
    # =====================================================

    sync_schema_registry(
        schema_registry=(schema_registry),
        display_registry=reg,
    )

    # =====================================================
    # Metrics Display Overlays
    # =====================================================

    sync_metrics_registry(
        metrics_registry=(metrics_registry),
        display_registry=reg,
    )

    # =====================================================
    # Explicit Manual Display Overlays
    # =====================================================

    register_all_display_fields(
        reg,
    )

    # =====================================================
    # Display Groups
    # =====================================================

    register_display_groups(
        reg,
    )

    # =====================================================
    # Display Views
    # =====================================================

    register_display_views(
        reg,
    )

    # =====================================================
    # Validation
    # =====================================================

    reg.validate()

    return reg
