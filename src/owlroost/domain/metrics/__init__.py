# src/owlroost/domain/metrics/__init__.py
"""
Metrics domain package.

Importing this module does NOT automatically register metrics.
Call `load_metrics()` explicitly when needed.
"""


def load_metrics():
    # 1. Load core/base metrics
    from . import metric_definitions

    # 2. Load modular definitions (spending, risk, etc.)
    from .definitions import load as load_defs

    load_defs()

    # 3. Load groups (depends on metrics)
    # 4. Load views LAST (depends on everything)
    from . import group_definitions, view_definitions
