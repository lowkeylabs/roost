# src/owlroost/metrics/plugins/balance_sheet.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
Balance sheet metrics.

Notes
-----
Synthetic financial metrics derived from:

    - OWL case inputs
    - HFP summaries

These metrics expose household balance-sheet
concepts as first-class semantic entities.
"""

from __future__ import annotations

from typing import Any

from owlroost.catalog.ontology import (
    CatalogNodeType,
)
from owlroost.core.utils import (
    normalize_module_path,
)
from owlroost.display.operations.normalize import (
    get_units_multiplier,
)
from owlroost.metrics.specs import (
    MetricSpec,
)

# =========================================================
# Ontology
# =========================================================


BALANCE_SHEET_VARIABLE: dict[str, Any] = dict(
    owner="ROOST",
    semantic_domain="decision",
    value_origin="roost-computed",
    projection_kind="synthetic",
    analytic_kind="primary",
    materialization_level="row",
    node_type=CatalogNodeType.VARIABLE,
    defined_in=normalize_module_path(__file__),
)

# =========================================================
# Helpers
# =========================================================


def _units_multiplier(row):
    inputs = row.get(
        "_inputs",
        {},
    )

    units = inputs.get(
        "solver_options",
        {},
    ).get(
        "units",
        "k",
    )

    return get_units_multiplier(
        units,
    )


def _input_list(row, section, field):
    inputs = row.get(
        "_inputs",
        {},
    )

    values = inputs.get(
        section,
        {},
    ).get(
        field,
        [],
    )
    return values


def _sum_input_list(
    row,
    section,
    field,
):
    values = _input_list(row, section, field)

    return sum(float(v or 0) for v in values) * _units_multiplier(row)


# =========================================================
# Savings
# =========================================================


def compute_total_taxable_savings(row):
    value = _sum_input_list(
        row,
        "savings_assets",
        "taxable_savings_balances",
    )
    return value


def compute_total_tax_deferred_savings(row):
    return _sum_input_list(
        row,
        "savings_assets",
        "tax_deferred_savings_balances",
    )


def compute_total_tax_free_savings(row):
    return _sum_input_list(
        row,
        "savings_assets",
        "tax_free_savings_balances",
    )


def compute_total_savings(row):
    return (
        compute_total_taxable_savings(row)
        + compute_total_tax_deferred_savings(row)
        + compute_total_tax_free_savings(row)
    )


# =========================================================
# HFP-backed Metrics
# =========================================================


def compute_fixed_assets_current_asset_value(row):
    return 0


def compute_fixed_assets_remain_debt_balances(row):
    return 0


# =========================================================
# Synthetic Balance Sheet Metrics
# =========================================================


def compute_total_assets(row):
    return compute_total_savings(row) + compute_fixed_assets_current_asset_value(row)


def compute_total_liabilities(row):
    return compute_fixed_assets_remain_debt_balances(row)


def compute_net_worth(row):
    return compute_total_savings(row) - compute_total_liabilities(row)


# =========================================================
# Plugin
# =========================================================


class BalanceSheetMetricsPlugin:
    """
    Register balance-sheet metrics.
    """

    def register(
        self,
        reg,
    ):
        metrics = [
            # ---------------------------------------------
            # Savings
            # ---------------------------------------------
            MetricSpec(
                name="balance_sheet.total_taxable_savings",
                dtype=float,
                compute_fn=compute_total_taxable_savings,
                aggregatable=False,
                description="Total taxable savings.",
                derived_from=[
                    "savings_assets.taxable_savings_balances",
                ],
                **BALANCE_SHEET_VARIABLE,
            ),
            MetricSpec(
                name="balance_sheet.total_tax_deferred_savings",
                dtype=float,
                compute_fn=compute_total_tax_deferred_savings,
                aggregatable=False,
                description="Total tax-deferred savings.",
                derived_from=[
                    "savings_assets.tax_deferred_savings_balances",
                ],
                **BALANCE_SHEET_VARIABLE,
            ),
            MetricSpec(
                name="balance_sheet.total_tax_free_savings",
                dtype=float,
                compute_fn=compute_total_tax_free_savings,
                aggregatable=False,
                description="Total tax-free savings.",
                derived_from=[
                    "savings_assets.tax_free_savings_balances",
                ],
                **BALANCE_SHEET_VARIABLE,
            ),
            MetricSpec(
                name="balance_sheet.total_savings",
                dtype=float,
                compute_fn=compute_total_savings,
                aggregatable=False,
                description="Total retirement savings.",
                derived_from=[
                    "balance_sheet.total_taxable_savings",
                    "balance_sheet.total_tax_deferred_savings",
                    "balance_sheet.total_tax_free_savings",
                ],
                **BALANCE_SHEET_VARIABLE,
            ),
            # ---------------------------------------------
            # Canonical HFP Values
            # ---------------------------------------------
            MetricSpec(
                name="balance_sheet.fixed_assets_current_value",
                dtype=float,
                compute_fn=compute_fixed_assets_current_asset_value,
                aggregatable=False,
                description="Total current fixed assets value from HFP.",
                derived_from=[
                    "household_financial_profile",
                ],
                **BALANCE_SHEET_VARIABLE,
            ),
            MetricSpec(
                name="balance_sheet.fixed_assets_debt_remaining_value",
                dtype=float,
                compute_fn=compute_fixed_assets_remain_debt_balances,
                aggregatable=False,
                description="Total remaining debt balance from HFP.",
                derived_from=[
                    "household_financial_profile",
                ],
                **BALANCE_SHEET_VARIABLE,
            ),
            # ---------------------------------------------
            # Synthetic Balance Sheet
            # ---------------------------------------------
            MetricSpec(
                name="balance_sheet.total_assets",
                dtype=float,
                compute_fn=compute_total_assets,
                aggregatable=False,
                description="Total assets.",
                derived_from=[
                    "balance_sheet.total_savings",
                    "balance_sheet.fixed_assets_current_value",
                ],
                **BALANCE_SHEET_VARIABLE,
            ),
            MetricSpec(
                name="balance_sheet.total_liabilities",
                dtype=float,
                compute_fn=compute_total_liabilities,
                aggregatable=False,
                description="Total assets.",
                derived_from=[
                    "balance_sheet.fixed_assets_debt_remaining_value",
                ],
                **BALANCE_SHEET_VARIABLE,
            ),
            MetricSpec(
                name="balance_sheet.net_worth",
                dtype=float,
                compute_fn=compute_net_worth,
                aggregatable=False,
                description="Household net worth.",
                derived_from=[
                    "balance_sheet.total_assets",
                    "balance_sheet.total_liabilities",
                ],
                **BALANCE_SHEET_VARIABLE,
            ),
            MetricSpec(
                name="balance_sheet.has_hfp_file",
                dtype=bool,
                compute_fn=lambda row: _input_list(
                    row, "household_financial_profile", "HFP_file_name"
                )
                != "None",
                aggregatable=False,
                description="Household net worth.",
                derived_from=[
                    "balance_sheet.total_savings",
                    "balance_sheet.total_liabilities",
                ],
                **BALANCE_SHEET_VARIABLE,
            ),
        ]

        for metric in metrics:
            reg.register(
                metric,
            )
