# src/owlroost/domain/metrics/__init__.py
"""
Metrics domain package.

Importing this module does NOT automatically register metrics.
Call `load_metrics()` explicitly when needed.
"""


def load_metrics():
    """
    Ensure all metrics, groups, and views are registered.

    Safe to call multiple times.
    """

    # ----------------------------------------
    # Core metrics
    # ----------------------------------------
    from . import metric_definitions  # noqa: F401

    # ----------------------------------------
    # Modular metric definitions
    # ----------------------------------------
    from .definitions import load as load_defs

    load_defs()

    # ----------------------------------------
    # Groups
    # ----------------------------------------
    from . import group_definitions

    if hasattr(group_definitions, "register_groups"):
        group_definitions.register_groups()

    # ----------------------------------------
    # Views (CRITICAL FIX)
    # ----------------------------------------
    from . import view_definitions

    if hasattr(view_definitions, "register_views"):
        view_definitions.register_views()
