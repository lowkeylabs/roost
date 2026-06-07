# src/owlroost/display/fields/__init__.py
#
# Copyright (c) 2026 John Leonard
# All rights reserved.
# SPDX-License-Identifier: LicenseRef-OwlRoost-Proprietary
# See LICENSE file in repository root.

"""
Display field module discovery.

Notes
-----
Display field definitions are distributed
across modules within this package.

Any module that exports:

    register_display_fields(reg)

will be automatically discovered and
executed during bootstrap.

Module Load Order
-----------------
Modules are loaded in lexicographic
filename order.

Recommended naming:

    01_identity.py
    02_methodology.py
    03_runtime.py
    04_scaling.py
    05_provenance.py
    06_balances.py
    07_catalog.py

This provides explicit, deterministic
registration ordering without requiring
manual imports.
"""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from types import ModuleType

# =========================================================
# Discovery
# =========================================================


def discover_display_modules() -> list[ModuleType]:
    """
    Discover display field modules.

    Returns
    -------
    list[ModuleType]
        Modules sorted by filename.
    """

    modules: list[ModuleType] = []

    package_path = Path(__file__).parent

    for module_info in sorted(
        pkgutil.iter_modules([str(package_path)]),
        key=lambda m: m.name,
    ):
        if module_info.name.startswith("_"):
            continue

        module = importlib.import_module(f"{__name__}.{module_info.name}")

        modules.append(module)

    return modules


# =========================================================
# Registration
# =========================================================


def register_all_display_fields(
    reg,
):
    """
    Register all display field modules.

    Any module providing:

        register_display_fields(reg)

    will be invoked automatically.

    Modules lacking that function
    are ignored.
    """

    for module in discover_display_modules():
        register_fn = getattr(
            module,
            "register_display_fields",
            None,
        )

        if register_fn is None:
            continue

        register_fn(reg)
