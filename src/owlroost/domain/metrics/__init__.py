"""
Metrics domain package.

Importing this module does NOT automatically register metrics.
Call `load_metrics()` explicitly when needed.
"""


def load_metrics():
    from . import (
        group_definitions,
        metric_definitions,  # keep for now (rest of metrics)
        view_definitions,
    )
    from .definitions import load as load_defs

    load_defs()
