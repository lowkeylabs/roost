# src/owlroost/display/explain/__init__.py
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

from owlroost.display.explain.bootstrap import (
    build_explanation_cell,
    build_field_explanation,
)
from owlroost.display.explain.specs import (
    parse_explain_request,
)

__all__ = [
    "parse_explain_request",
    "build_field_explanation",
    "build_explanation_cell",
]
