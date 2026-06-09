# src/owlroost/metrics/plugins/balance_sheet_metrics.py
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

BALANCE_SHEET_SYNTHETIC: dict[str, Any] = dict(
    owner="ROOST",
    semantic_domain="decision",
    value_origin="roost-computed",
    projection_kind="synthetic",
    analytic_kind="synthetic",
    materialization_level="case",
    node_type=CatalogNodeType.VARIABLE,
    defined_in=normalize_module_path(__file__),
)

BALANCE_SHEET_CANONICAL: dict[str, Any] = dict(
    owner="ROOST",
    semantic_domain="decision",
    value_origin="roost-computed",
    projection_kind="canonical",
    analytic_kind="observed",
    materialization_level="case",
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


def _sum_input_list(
    row,
    section,
    field,
):
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


def compute_fixed_assets(row):
    return float(
        row.get(
            "_hfp",
            {},
        ).get(
            "total_fixed_assets",
            0.0,
        )
    )


def compute_total_liabilities(row):
    return float(
        row.get(
            "_hfp",
            {},
        ).get(
            "total_debts",
            0.0,
        )
    )


def compute_residence_value(row):
    return float(
        row.get(
            "_hfp",
            {},
        ).get(
            "residence_value",
            0.0,
        )
    )


def compute_mortgage_debt(row):
    return float(
        row.get(
            "_hfp",
            {},
        ).get(
            "mortgage_debt",
            0.0,
        )
    )


# =========================================================
# Synthetic Balance Sheet Metrics
# =========================================================


def compute_net_hfp_assets(row):
    return compute_fixed_assets(row) - compute_total_liabilities(row)


def compute_total_assets(row):
    return compute_total_savings(row) + compute_fixed_assets(row)


def compute_net_worth(row):
    return compute_total_savings(row) + compute_net_hfp_assets(row)


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
                **BALANCE_SHEET_SYNTHETIC,
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
                **BALANCE_SHEET_SYNTHETIC,
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
                **BALANCE_SHEET_SYNTHETIC,
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
                **BALANCE_SHEET_SYNTHETIC,
            ),
            # ---------------------------------------------
            # Canonical HFP Values
            # ---------------------------------------------
            MetricSpec(
                name="balance_sheet.fixed_assets",
                dtype=float,
                compute_fn=compute_fixed_assets,
                aggregatable=False,
                description="Total fixed assets.",
                derived_from=[
                    "household_financial_profile",
                ],
                **BALANCE_SHEET_CANONICAL,
            ),
            MetricSpec(
                name="balance_sheet.total_liabilities",
                dtype=float,
                compute_fn=compute_total_liabilities,
                aggregatable=False,
                description="Total liabilities.",
                derived_from=[
                    "household_financial_profile",
                ],
                **BALANCE_SHEET_CANONICAL,
            ),
            MetricSpec(
                name="balance_sheet.residence_value",
                dtype=float,
                compute_fn=compute_residence_value,
                aggregatable=False,
                description="Residence value.",
                derived_from=[
                    "household_financial_profile",
                ],
                **BALANCE_SHEET_CANONICAL,
            ),
            MetricSpec(
                name="balance_sheet.mortgage_debt",
                dtype=float,
                compute_fn=compute_mortgage_debt,
                aggregatable=False,
                description="Mortgage debt.",
                derived_from=[
                    "household_financial_profile",
                ],
                **BALANCE_SHEET_CANONICAL,
            ),
            # ---------------------------------------------
            # Synthetic Balance Sheet
            # ---------------------------------------------
            MetricSpec(
                name="balance_sheet.net_hfp_assets",
                dtype=float,
                compute_fn=compute_net_hfp_assets,
                aggregatable=False,
                description="Fixed assets minus liabilities.",
                derived_from=[
                    "balance_sheet.fixed_assets",
                    "balance_sheet.total_liabilities",
                ],
                **BALANCE_SHEET_SYNTHETIC,
            ),
            MetricSpec(
                name="balance_sheet.total_assets",
                dtype=float,
                compute_fn=compute_total_assets,
                aggregatable=False,
                description="Total assets.",
                derived_from=[
                    "balance_sheet.total_savings",
                    "balance_sheet.fixed_assets",
                ],
                **BALANCE_SHEET_SYNTHETIC,
            ),
            MetricSpec(
                name="balance_sheet.net_worth",
                dtype=float,
                compute_fn=compute_net_worth,
                aggregatable=False,
                description="Household net worth.",
                derived_from=[
                    "balance_sheet.total_savings",
                    "balance_sheet.net_hfp_assets",
                ],
                **BALANCE_SHEET_SYNTHETIC,
            ),
        ]

        for metric in metrics:
            reg.register(
                metric,
            )
