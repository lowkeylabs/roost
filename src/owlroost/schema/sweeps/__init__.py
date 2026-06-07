# src/owlroost/schema/sweeps/__init__.py
#
# Copyright (c) 2026 John Leonard
# All rights reserved.
# SPDX-License-Identifier: LicenseRef-OwlRoost-Proprietary
# See LICENSE file in repository root.

"""
Sweep field discovery and expansion.

Notes
-----
Hydra sweep variables are distributed
across modules within this package.

Each module may export:

    register_schema_fields(reg)

and/or:

    expand(run_dict)

Discovery is automatic.

Architectural Invariant
-----------------------
Each sweep module owns:

    - schema registration
    - ontology metadata
    - sweep expansion logic

The package owns:

    - module discovery
    - registration dispatch
    - expansion dispatch
"""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from types import ModuleType

# =========================================================
# Discovery
# =========================================================


def _discover_sweep_modules() -> list[ModuleType]:
    """
    Discover sweep modules.

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
# Schema Registration
# =========================================================


def register_sweeps(
    reg,
):
    """
    Register all sweep schema fields.

    Any module exporting:

        register_schema_fields(reg)

    will be invoked automatically.

    Modules lacking that function
    are ignored.
    """

    for module in _discover_sweep_modules():
        register_fn = getattr(
            module,
            "register_schema_fields",
            None,
        )

        if register_fn is None:
            continue

        register_fn(
            reg,
        )


# =========================================================
# Sweep Expansion
# =========================================================


def expand_sweeps(
    run_dict,
):
    """
    Expand all registered sweep variables.

    Any module exporting:

        expand(run_dict)

    will be invoked automatically.

    Modules lacking that function
    are ignored.

    Parameters
    ----------
    run_dict:
        Runtime configuration dictionary.

    Returns
    -------
    dict
        Expanded runtime configuration.
    """

    for module in _discover_sweep_modules():
        expand_fn = getattr(
            module,
            "expand",
            None,
        )

        if expand_fn is None:
            continue

        expand_fn(
            run_dict,
        )

    return run_dict
