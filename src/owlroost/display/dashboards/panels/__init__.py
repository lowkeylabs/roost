# src/owlroost/display/dashboards/panels/__init__.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
Dashboard panel plugin discovery.

Notes
-----
Discovers dashboard panel implementations and
registers their materializers.

Each panel module must export:

    PANEL_SPEC
        Dashboard panel spec class.

    materialize()
        Panel materializer.

Example
-------

    # counter.py

    PANEL_SPEC = CounterPanel

    def materialize(...):
        ...

Architecture
------------

Panel Spec
    ->
Panel Materializer
    ->
RoostDashboardPanel

New panel types become available simply by
dropping a module into this package.
"""

from __future__ import annotations

import importlib
import pkgutil

# =========================================================
# Registry
# =========================================================

_PANEL_MATERIALIZERS = {}

# =========================================================
# Discovery
# =========================================================

for module_info in pkgutil.iter_modules(
    __path__,
):
    module = importlib.import_module(
        f"{__name__}.{module_info.name}",
    )

    panel_spec = getattr(
        module,
        "PANEL_SPEC",
        None,
    )

    materialize = getattr(
        module,
        "materialize",
        None,
    )

    if panel_spec is not None and materialize is not None:
        _PANEL_MATERIALIZERS[panel_spec] = materialize

# =========================================================
# Lookup
# =========================================================


def get_panel_materializer_for_spec(
    panel_spec,
):
    """
    Return materializer for panel instance.
    """

    spec_type = type(
        panel_spec,
    )

    try:
        return _PANEL_MATERIALIZERS[spec_type]

    except KeyError as exc:
        raise KeyError(
            f"No dashboard panel materializer registered for {spec_type.__name__}"
        ) from exc


def registered_panel_specs():
    """
    Return registered panel spec classes.
    """

    return sorted(spec.__name__ for spec in _PANEL_MATERIALIZERS)


def get_panel_materializer(
    panel_type,
):
    try:
        return _PANEL_MATERIALIZERS[panel_type]

    except KeyError as exc:
        raise KeyError(f"Dashboard panel not registered: {panel_type.__name__}") from exc
