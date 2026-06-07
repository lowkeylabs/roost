# src/owlroost/schema/sections/__init__.py
#
# Copyright (c) 2026 John Leonard
# All rights reserved.
# SPDX-License-Identifier: LicenseRef-OwlRoost-Proprietary
# See LICENSE file in repository root.

"""
Schema section discovery.

Notes
-----
ROOST schema sections are distributed
across modules within this package.

Any module exporting:

    register_schema_fields(reg)

will be automatically discovered and
executed during bootstrap.
"""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path


def register_sections(
    reg,
):
    """
    Register all schema sections.
    """

    package_path = Path(__file__).parent

    for module_info in sorted(
        pkgutil.iter_modules([str(package_path)]),
        key=lambda m: m.name,
    ):
        if module_info.name.startswith("_"):
            continue

        module = importlib.import_module(f"{__name__}.{module_info.name}")

        register_fn = getattr(
            module,
            "register_schema_fields",
            None,
        )

        if register_fn is None:
            continue

        register_fn(reg)
