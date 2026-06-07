# src/owlroost/display/explain/facets/__init__.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
Explain facet discovery.

Notes
-----
Owns discovery and registration of
explanation facets.

Architectural Invariant
-----------------------

Each facet module must export:

    FACET_NAME

and:

    render(...)

Example
-------

FACET_NAME = "ontology"

def render(
    *,
    display_field,
    catalog_row,
    row_values,
):
    ...

Available facets are discovered
automatically.

Adding a new facet requires only:

    display/explain/facets/<name>.py

No modifications to bootstrap.py,
specs.py, or materializers are required.
"""

from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Callable
from pathlib import Path

# =========================================================
# Registry
# =========================================================

FACETS: dict[
    str,
    Callable,
] = {}

# =========================================================
# Discovery
# =========================================================


def load_facets() -> dict[str, Callable]:
    """
    Discover and register explain facets.
    """

    FACETS.clear()

    package_path = Path(
        __file__,
    ).parent

    for module_info in pkgutil.iter_modules(
        [str(package_path)],
    ):
        if module_info.name.startswith(
            "_",
        ):
            continue

        module = importlib.import_module(
            f"{__name__}.{module_info.name}",
        )

        facet_name = getattr(
            module,
            "FACET_NAME",
            None,
        )

        render_fn = getattr(
            module,
            "render",
            None,
        )

        if facet_name is None or render_fn is None:
            continue

        FACETS[facet_name] = render_fn

    return FACETS


# =========================================================
# Bootstrap
# =========================================================

load_facets()

# =========================================================
# Public API
# =========================================================

AVAILABLE_EXPLAIN_FACETS = set(FACETS) | {"all"}

__all__ = [
    "FACETS",
    "AVAILABLE_EXPLAIN_FACETS",
    "load_facets",
]
