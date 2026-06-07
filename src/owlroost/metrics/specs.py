# src/owlroost/metrics/specs.py
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

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from owlroost.catalog.ontology import OntologySpec


@dataclass(kw_only=True)
class MetricSpec(OntologySpec):
    """
    Canonical semantic definition
    of an observable runtime metric.

    Notes
    -----
    MetricSpec defines semantic ontology
    for values materialized through:

        - OWL execution
        - ROOST orchestration
        - aggregation systems
        - analytical synthesis

    These specifications are harvested by:

        - MetricsRegistry
        - catalog subsystem
        - aggregation systems
        - explainability systems
        - reporting pipelines

    MetricSpec also records authoring
    metadata used during catalog provenance
    synthesis.

    Ontology semantics are inherited from:

        OntologySpec
    """

    # =====================================================
    # Identity
    # =====================================================

    name: str

    category: str = "metric"

    description: str = ""

    # =====================================================
    # Authoring metadata (different from catalog provenance)
    # =====================================================

    defined_in: str | None = None

    # =====================================================
    # Typing
    # =====================================================

    dtype: type | None = object

    # =====================================================
    # Materialization
    # =====================================================

    compute_fn: Callable[[dict[str, Any]], Any] | None = None

    # =====================================================
    # Aggregation
    # =====================================================

    aggregatable: bool = True

    default_aggregates: list[str] = field(default_factory=list)

    # =====================================================
    # Aggregate Metadata
    # =====================================================

    aggregate_function: str | None = None

    # =====================================================
    # Notes
    # =====================================================

    notes: str = ""
