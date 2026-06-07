# src/owlroost/display/dashboards/layouts/__init__.py
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

import importlib
import pkgutil
from pathlib import Path


def register_dashboards(
    reg,
):
    package_path = Path(
        __file__,
    ).parent

    for module_info in pkgutil.iter_modules(
        [str(package_path)],
    ):
        if module_info.name.startswith("_"):
            continue

        module = importlib.import_module(
            f"{__name__}.{module_info.name}",
        )

        fn = getattr(
            module,
            "register_display_dashboards",
            None,
        )

        if fn:
            fn(reg)
