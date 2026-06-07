# src/owlroost/schema/sweeps/ss_age_pair.py
#
# Copyright (c) 2026 John Leonard
# All rights reserved.
# SPDX-License-Identifier: LicenseRef-OwlRoost-Proprietary
# See LICENSE file in repository root.

"""
fixed_income.ss_age_pair sweep variable.
"""

from __future__ import annotations

from owlroost.catalog.ontology import (
    CatalogNodeType,
)

from ..registry import (
    FieldSpec,
)


def register_schema_fields(
    reg,
):
    reg.register(
        FieldSpec(
            name="roost_sweeps.ss_age_pair",
            dtype=str,
            path=(
                "roost_sweeps",
                "ss_age_pair",
            ),
            source="sweep",
            owner="ROOST",
            semantic_domain="decision",
            value_origin="user-specified",
            projection_kind="canonical",
            analytic_kind="observed",
            materialization_level="run",
            node_type=CatalogNodeType.VARIABLE,
            expands_to=[
                "fixed_income.social_security_ages",
            ],
            description=("Social Security claiming age pair formatted as AA.A-AA.A."),
            defined_in="ss_age_pair",
        )
    )


def expand(
    run_dict,
):
    roost_sweeps = run_dict.setdefault("roost_sweeps", {})
    value = roost_sweeps.pop(
        "ss_age_pair",
        None,
    )

    if not value:
        return

    p1, p2 = value.split(
        "-",
        1,
    )

    fixed_income = run_dict.setdefault(
        "fixed_income",
        {},
    )

    fixed_income["social_security_ages"] = [
        float(p1),
        float(p2),
    ]
