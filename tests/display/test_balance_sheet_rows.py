# tests/display/test_balance_sheet_rows.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
Balance-sheet row integration tests.

Notes
-----
Verify canonical balance-sheet
metrics are present on rows produced
by loaders.
"""

from __future__ import annotations

from pathlib import Path

from owlroost.display.loaders import (
    load_case_rows,
)
from owlroost.metrics.bootstrap import (
    build_metrics_registry,
)

CASES_DIR = Path(__file__).parents[1] / "end_to_end" / "cases"

REQUIRED_METRICS = [
    "balance_sheet.net_worth",
    "balance_sheet.total_assets",
    "balance_sheet.total_liabilities",
    "balance_sheet.total_savings",
    "balance_sheet.fixed_assets_current_value",
]


# =========================================================
# Helpers
# =========================================================


def assert_balance_sheet_metrics(
    row,
):
    metrics = row["_metrics"]

    for metric in REQUIRED_METRICS:
        assert metric in metrics

        assert metrics[metric] is not None


# =========================================================
# Case Rows
# =========================================================


def test_case_rows_contain_balance_sheet_metrics():
    """
    Case rows should expose
    balance-sheet metrics.
    """

    metrics_registry = build_metrics_registry()

    rows = load_case_rows(
        CASES_DIR,
        metrics_registry=metrics_registry,
    )

    assert rows

    assert_balance_sheet_metrics(
        rows[0],
    )
