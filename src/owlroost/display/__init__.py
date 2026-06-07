# src/owlroost/display/__init__.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

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
