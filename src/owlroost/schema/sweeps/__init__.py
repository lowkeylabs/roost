# src/owlroost/schema/sweeps/__init__.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
Sweep field discovery, CLI expansion,
and canonical materialization.

Notes
-----
Hydra sweep variables are distributed
across modules within this package.

Each module may export:

    register_schema_fields(reg)

    expand_cli_to_override(
        override: str,
    )

    materialize_override_to_canonical(
        run_dict,
    )

Discovery is automatic.

Architectural Invariant
-----------------------
Each sweep module owns:

    - schema registration
    - ontology metadata
    - CLI expansion logic
    - canonical materialization logic

The package owns:

    - module discovery
    - registration dispatch
    - expansion dispatch
    - materialization dispatch
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

        modules.append(
            module,
        )

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
# CLI Expansion
# =========================================================


def expand_cli_overrides(
    overrides: list[str],
) -> list[str]:
    """
    Expand sweep-specific CLI syntax
    into Hydra-compatible overrides.

    Any module exporting:

        expand_cli_to_override(
            override: str,
        )

    will be invoked automatically.

    Modules lacking that function
    are ignored.
    """

    expanded: list[str] = []

    for override in overrides:
        handled = False

        for module in _discover_sweep_modules():
            expand_fn = getattr(
                module,
                "expand_cli_to_override",
                None,
            )

            if expand_fn is None:
                continue

            result = expand_fn(
                override,
            )

            if result is None:
                continue

            expanded.extend(
                result,
            )

            handled = True

            break

        if not handled:
            expanded.append(
                override,
            )

    return expanded


# =========================================================
# Canonical Materialization
# =========================================================


def materialize_sweeps(
    run_dict,
):
    """
    Materialize all registered sweep
    overrides into canonical variables.

    Any module exporting:

        materialize_override_to_canonical(
            run_dict,
        )

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
        Runtime configuration with
        sweep variables materialized
        into canonical variables.
    """

    for module in _discover_sweep_modules():
        materialize_fn = getattr(
            module,
            "materialize_override_to_canonical",
            None,
        )

        if materialize_fn is None:
            continue

        materialize_fn(
            run_dict,
        )

    return run_dict
