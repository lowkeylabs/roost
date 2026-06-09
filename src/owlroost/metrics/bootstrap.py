# src/owlroost/metrics/bootstrap.py
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

from owlroost.metrics.registry import (
    MetricsRegistry,
)

from .plugins.balance_sheet_metrics import BalanceSheetMetricsPlugin
from .plugins.execution_metrics import ExecutionMetricsPlugin
from .plugins.hydra_overrides import HydraOverridesPlugin
from .plugins.output_metrics import OutputMetricsPlugin

# =========================================================
# Bootstrap
# =========================================================


def build_metrics_registry():
    """
    Construct MetricsRegistry.

    MetricsRegistry defines the canonical
    semantic model for OUTPUT metrics.

    This registry is intentionally independent
    from runtime metric generation.

    Responsibilities:
        - metric names
        - dtypes
        - descriptions
        - aggregation defaults
        - compute levels
        - display hints

    Runtime metric synthesis belongs to:

        metrics/builders.py
    """

    reg = MetricsRegistry()

    # =====================================================
    # Register canonical output metrics
    # =====================================================

    OutputMetricsPlugin().register(reg)
    ExecutionMetricsPlugin().register(reg)
    HydraOverridesPlugin().register(reg)
    BalanceSheetMetricsPlugin().register(reg)

    return reg
