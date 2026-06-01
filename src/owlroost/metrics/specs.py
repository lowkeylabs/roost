# src/owlroost/metrics/specs.py

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


@dataclass
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
    # Provenance
    # =====================================================

    defined_in: str | None = None

    derived_from: list[str] = field(default_factory=list)

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
