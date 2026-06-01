# src/owlroost/display/__init__.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from .registry import (
    DisplayRegistry,
)
from .specs import (
    DisplayField,
    DisplayGroup,
    DisplayProfile,
    DisplayView,
)

__all__ = [
    "DisplayRegistry",
    "DisplayField",
    "DisplayGroup",
    "DisplayProfile",
    "DisplayView",
]
