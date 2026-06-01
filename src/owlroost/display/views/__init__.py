# src/owlroost/display/views/__init__.py

"""
Display views discovery.

Notes
-----
Display views are distributed across
modules within this package.

Any module exporting:

    register_display_views(reg)

will be automatically discovered and
executed during bootstrap.

Module Load Order
-----------------
Modules are loaded in lexicographic
filename order.

Recommended naming:

    01_core.py
    02_execution.py
    03_financial.py
    04_provenance.py

Multiple modules may share the same
numeric prefix.

Examples:

    01_identity.py
    01_runtime_identity.py

    02_execution.py
    02_runtime.py

This allows grouping by phase while
maintaining deterministic ordering.
"""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from types import ModuleType

# =========================================================
# Discovery
# =========================================================


def discover_view_modules() -> list[ModuleType]:
    """
    Discover view modules.

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


def register_display_views(
    reg,
):
    """
    Register all display view modules.

    Any module providing:

        register_display_views(reg)

    will be invoked automatically.
    """

    for module in discover_view_modules():
        register_fn = getattr(
            module,
            "register_display_views",
            None,
        )

        if register_fn is None:
            continue

        register_fn(reg)


__all__ = [
    "register_display_views",
]
