# src/owlroost/display/explain/specs.py
#
# Copyright (c) 2026 John Leonard
# All rights reserved.
# SPDX-License-Identifier: LicenseRef-OwlRoost-Proprietary
# See LICENSE file in repository root.

"""
Display explanation specifications.

Notes
-----
Owns explain request parsing,
normalization, and validation.

Architectural Invariant
-----------------------

Available explain facets are discovered
from the facet registry.

This module does NOT maintain a hard-coded
list of explain facets.

Facet registration is owned by:

    display.explain.facets
"""

from __future__ import annotations

from collections.abc import Iterable

from owlroost.display.explain.facets import (
    AVAILABLE_EXPLAIN_FACETS,
)

# =========================================================
# Explain Request Parsing
# =========================================================


def parse_explain_request(
    explain: str | Iterable[str] | None,
) -> tuple[set[str], list[str]]:
    """
    Parse explain request.

    Returns
    -------
    tuple[set[str], list[str]]

        (
            normalized_facets,
            errors,
        )

    Examples
    --------

    "variables"

        (
            {"variables"},
            [],
        )

    "variables,bogus"

        (
            {"variables"},
            ["Unknown explain facet: bogus"],
        )
    """

    if explain is None:
        return set(), []

    if isinstance(
        explain,
        str,
    ):
        requested = {item.strip() for item in explain.split(",") if item.strip()}

    else:
        requested = {str(item).strip() for item in explain if str(item).strip()}

    errors = []

    unknown = sorted(requested - AVAILABLE_EXPLAIN_FACETS)

    for facet in unknown:
        errors.append(f"Unknown explain facet: {facet}")

    facets = requested & AVAILABLE_EXPLAIN_FACETS

    if "all" in facets:
        facets.remove(
            "all",
        )

        facets |= AVAILABLE_EXPLAIN_FACETS - {"all"}

    return (
        facets,
        errors,
    )
