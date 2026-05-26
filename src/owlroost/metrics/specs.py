from __future__ import annotations

from dataclasses import (
    dataclass,
    field,
)

from owlroost.display.specs import (
    DisplayProfile,
)


@dataclass
class MetricFieldSpec:
    """
    Canonical semantic definition
    of an output metric.
    """

    # =====================================================
    # Identity
    # =====================================================

    name: str

    category: str = "metric"

    description: str = ""

    # =====================================================
    # Metric Semantics
    # =====================================================

    compute_level: str = "trial"

    # Valid examples:
    #
    #   trial
    #   run
    #   experiment
    #   case
    #   synthetic

    # =====================================================
    # Typing
    # =====================================================

    dtype: type = object

    # =====================================================
    # Aggregation
    # =====================================================

    aggregatable: bool = True

    default_aggregates: list[str] = field(default_factory=list)

    # =====================================================
    # Default Display Profiles
    # =====================================================

    profiles: dict[str, DisplayProfile] = field(default_factory=dict)
