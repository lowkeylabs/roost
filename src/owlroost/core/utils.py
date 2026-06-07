# src/owlroost/core/utils.py
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

from pathlib import Path


def normalize_module_path(
    file_name,
):
    p = Path(file_name)

    parts = p.parts

    try:
        idx = parts.index("owlroost")

        return "/".join(parts[idx + 1 :])

    except ValueError:
        return p.name
