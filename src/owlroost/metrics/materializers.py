# src/owlroost/metrics/materializers.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
Metric materialization helpers.

Notes
-----
Materializes MetricSpec compute_fn values
into row["_metrics"].

Architectural Responsibilities
------------------------------
    - evaluate synthetic metrics
    - respect materialization level
    - isolate metric execution from
      loaders and discovery systems

This module intentionally does not
perform aggregation.

Aggregation belongs to:

    metrics/aggregation/
"""

from __future__ import annotations

# =========================================================
# Public API
# =========================================================


def materialize_row_metrics(
    row,
    metrics_registry,
):
    """
    Materialize MetricSpec values into
    row["_metrics"].

    Parameters
    ----------
    row
        Canonical row structure.

    metrics_registry
        MetricsRegistry instance.

    Notes
    -----
    Only metrics matching:

        metric.materialization_level

    are evaluated.

    Existing metric values are preserved.
    """

    level = row.get(
        "_meta",
        {},
    ).get(
        "level",
    )

    metrics = row.setdefault(
        "_metrics",
        {},
    )

    for metric in metrics_registry.all():
        # =============================================
        # Skip non-computed metrics
        # =============================================

        if metric.compute_fn is None:
            continue

        # =============================================
        # Respect materialization level
        # =============================================

        #        if metric.materialization_level and metric.materialization_level != level:
        #            continue

        if metric.materialization_level not in {
            level,
            "row",
        }:
            continue

        # =============================================
        # Preserve existing values
        # =============================================

        if metric.name in metrics:
            continue

        # =============================================
        # Compute metric
        # =============================================

        try:
            value = metric.compute_fn(
                row,
            )

        except Exception:
            continue

        metrics[metric.name] = value

    return row
