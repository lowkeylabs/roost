# src/owlroost/schema/sweeps/ss_age_person1.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
Social Security claiming age sweep for person 1.
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
            name="roost_sweeps.ss_age_person1",
            dtype=float,
            path=(
                "roost_sweeps",
                "ss_age_person1",
            ),
            source="sweep",
            owner="ROOST",
            semantic_domain="decision",
            value_origin="user-specified",
            projection_kind="canonical",
            analytic_kind="observed",
            materialization_level="run",
            node_type=CatalogNodeType.VARIABLE,
            materializes_to=[
                "fixed_income.social_security_ages",
            ],
            description=("Social Security claiming age for person 1."),
            defined_in="ss_age_person1",
        )
    )


def materialize_override_to_canonical(
    run_dict,
):
    roost_sweeps = run_dict.setdefault(
        "roost_sweeps",
        {},
    )

    value = roost_sweeps.pop(
        "ss_age_person1",
        None,
    )

    if value is None:
        return

    # -----------------------------------------------------
    # Existing ages
    # -----------------------------------------------------

    fixed_income = run_dict.setdefault(
        "fixed_income",
        {},
    )

    ages = fixed_income.get(
        "social_security_ages",
    )

    if ages is None:
        ages = []
    else:
        ages = list(
            ages,
        )

    # -----------------------------------------------------
    # Ensure slot 1 exists
    # -----------------------------------------------------

    while len(ages) <= 1:
        ages.append(
            None,
        )

    # -----------------------------------------------------
    # Apply override
    # -----------------------------------------------------

    ages[1] = float(
        value,
    )

    fixed_income["social_security_ages"] = ages
