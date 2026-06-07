# src/owlroost/display/operations/normalize.py
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


def get_input_units(
    inputs,
):
    """
    Resolve solver input units.

    Valid values:
        "1" = dollars
        "k" = thousands
        "M" = millions

    Default:
        "k"
    """

    return inputs.get("solver_options", {}).get("units", "k")


def get_units_multiplier(
    units,
):
    """
    Convert OWL units into dollar multiplier.
    """

    mapping = {
        "1": 1.0,
        "k": 1_000.0,
        "M": 1_000_000.0,
    }

    return mapping.get(
        units,
        1_000.0,
    )


def normalize_input_money(
    inputs,
    value,
):
    """
    Convert TOML-scaled money value into
    canonical dollars.
    """

    if value is None:
        return 0.0

    units = get_input_units(inputs)

    multiplier = get_units_multiplier(units)

    return float(value) * multiplier
