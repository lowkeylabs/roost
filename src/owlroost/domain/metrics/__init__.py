"""
Metrics domain package.

Importing this module does NOT automatically register metrics.
Call `load_metrics()` explicitly when needed.
"""


def load_metrics():
    # Local imports to avoid circular dependency
    from . import group_definitions, metric_definitions, view_definitions
