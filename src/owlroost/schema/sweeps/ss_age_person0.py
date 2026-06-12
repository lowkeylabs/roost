# src/owlroost/schema/sweeps/ss_age_person0.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
Social Security claiming age sweep for person 0.
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
            name="roost_sweeps.ss_age_person0",
            dtype=float,
            path=(
                "roost_sweeps",
                "ss_age_person0",
            ),
            source="sweep",
            owner="ROOST",
            semantic_domain="decision",
            value_origin="user-specified",
            projection_kind="synthetic",
            analytic_kind="primary",
            materialization_level="run",
            node_type=CatalogNodeType.VARIABLE,
            materializes_to=[
                "fixed_income.social_security_ages",
            ],
            description=("Social Security claiming age for person 0."),
            defined_in=normalize_module_path(__file__),
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
        "ss_age_person0",
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
    # Ensure slot 0 exists
    # -----------------------------------------------------

    while len(ages) <= 0:
        ages.append(
            None,
        )

    # -----------------------------------------------------
    # Apply override
    # -----------------------------------------------------

    ages[0] = float(
        value,
    )

    fixed_income["social_security_ages"] = ages
