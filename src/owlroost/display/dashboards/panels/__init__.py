# src/owlroost/display/dashboards/panels/__init__.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from .counter import (
    materialize_counter_panel,
)
from .crosstab import (
    materialize_crosstab_panel,
)
from .summary import (
    materialize_summary_panel,
)

__all__ = [
    "materialize_summary_panel",
    "materialize_counter_panel",
    "materialize_crosstab_panel",
]
