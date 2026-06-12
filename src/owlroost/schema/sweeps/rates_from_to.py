# src/owlroost/schema/sweeps/rates_from_to.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
rates_selection.from_to sweep variable.
"""

from __future__ import annotations

from owlroost.catalog.ontology import (
    CatalogNodeType,
)
from owlroost.core.utils import normalize_module_path

from ..registry import (
    FieldSpec,
)


def register_schema_fields(
    reg,
):
    reg.register(
        FieldSpec(
            name="roost_sweeps.rates_from_to",
            dtype=str,
            path=(
                "roost_sweeps",
                "rates_from_to",
            ),
            source="sweep",
            owner="ROOST",
            semantic_domain="design",
            value_origin="user-specified",
            projection_kind="synthetic",
            analytic_kind="primary",
            materialization_level="run",
            node_type=CatalogNodeType.VARIABLE,
            materializes_to=[
                "rates_selection.from",
                "rates_selection.to",
            ],
            description=("Historical market window formatted as YYYY-YYYY."),
            defined_in=normalize_module_path(__file__),
        )
    )


def materialize_override_to_canonical(
    run_dict,
):
    roost = run_dict.setdefault(
        "roost_sweeps",
        {},
    )

    value = roost.pop(
        "rates_from_to",
        None,
    )

    if not value:
        return

    start, end = value.split(
        "-",
        1,
    )

    rates = run_dict.setdefault(
        "rates_selection",
        {},
    )

    rates["from"] = int(start)
    rates["to"] = int(end)
