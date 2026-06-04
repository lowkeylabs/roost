# src/owlroost/catalog/comparison/__init__.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from .structure import (
    build_compare_entries,
    flatten_structure,
    format_compare_value,
    resolve_path,
    rows_are_equivalent,
    values_differ,
)
from .supersession import (
    collect_superseded_rows,
    find_superseded_rows,
)

__all__ = [
    # structure
    "build_compare_entries",
    "rows_are_equivalent",
    "format_compare_value",
    # supersession
    "collect_superseded_rows",
    "find_superseded_rows",
]
