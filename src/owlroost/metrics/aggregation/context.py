# src/owlroost/metrics/aggregation/context.py

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

# =========================================================
# Aggregation Context
# =========================================================


@dataclass(slots=True)
class AggregationContext:
    """
    Context object passed to aggregation explainers.

    This provides provenance and semantic metadata
    about an aggregation result.

    Example:
        aggregation = "mean"
        field_name = "elapsed_seconds"
        n_valid = 93
        n_total = 100

    Used by:
    - explain mode
    - report generation
    - hover/help systems
    - future provenance tracing
    """

    # -----------------------------------------------------
    # Aggregated values actually used
    # -----------------------------------------------------

    source_values: list[Any]

    # -----------------------------------------------------
    # Non-null values included
    # -----------------------------------------------------

    n_valid: int | None

    # -----------------------------------------------------
    # Total rows considered
    # -----------------------------------------------------

    n_total: int | None

    # -----------------------------------------------------
    # Aggregation name
    #
    # Examples:
    #   mean
    #   p10
    #   median
    # -----------------------------------------------------

    aggregation: str | None

    # -----------------------------------------------------
    # Field name being aggregated
    #
    # Examples:
    #   elapsed_seconds
    #   spending
    # -----------------------------------------------------

    field_name: str | None = None

    # -----------------------------------------------------
    # Dataset level
    #
    # Examples:
    #   trial
    #   run
    #   experiment
    # -----------------------------------------------------

    level: str | None = None

    # -----------------------------------------------------
    # Optional renderer/display metadata
    # -----------------------------------------------------

    fmt: str | None = None

    # -----------------------------------------------------
    # Optional provenance metadata
    # -----------------------------------------------------

    source: str | None = None


# =========================================================
# Explain Function Type
# =========================================================


type AggregationExplainFn = Callable[[AggregationContext], str]
