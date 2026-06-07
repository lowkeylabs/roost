# src/owlroost/metrics/aggregation/context.py
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

from collections.abc import (
    Callable,
)
from dataclasses import (
    dataclass,
)
from typing import (
    Any,
)

# =========================================================
# Aggregation Explain Context
# =========================================================


@dataclass(slots=True)
class AggregationContext:
    """
    Lightweight explainability metadata
    associated with an aggregate result.

    Notes
    -----
    This object intentionally supports:

        - explain mode
        - report generation
        - hover/help systems
        - analytical annotations

    while intentionally avoiding ownership of:

        - ontology semantics
        - provenance systems
        - catalog identity
        - rendering behavior

    Canonical semantic ownership belongs to:

        - OntologySpec
        - MetricSpec
        - CatalogSpec
    """

    # =====================================================
    # Aggregated Values
    # =====================================================

    source_values: list[Any]

    # =====================================================
    # Aggregation Statistics
    # =====================================================

    n_valid: int | None

    n_total: int | None

    # =====================================================
    # Aggregation Semantics
    # =====================================================

    aggregation: str | None

    field_name: str | None = None

    # =====================================================
    # Runtime Materialization
    # =====================================================

    materialization_level: str | None = None

    # =====================================================
    # Optional Display Metadata
    # =====================================================

    fmt: str | None = None


# =========================================================
# Explain Function Type
# =========================================================

type AggregationExplainFn = Callable[
    [AggregationContext],
    str,
]
