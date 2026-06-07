# src/owlroost/schema/sections/spending_policy.py
#
# Copyright (c) 2026 John Leonard
# All rights reserved.
# SPDX-License-Identifier: LicenseRef-OwlRoost-Proprietary
# See LICENSE file in repository root.

"""
Spending policy schema section.

Notes
-----
Defines ROOST spending policy inputs.

These variables describe spending
constraints and lifestyle targets that
supplement OWL retirement planning
configuration.

Architectural Invariant
-----------------------
This module owns:

    - section model
    - schema registration
    - ontology metadata

for the spending_policy TOML section.
"""

from __future__ import annotations

from pydantic import (
    Field,
)

from owlroost.catalog.ontology import (
    CatalogNodeType,
)
from owlroost.core.utils import normalize_module_path
from owlroost.schema.registry import (
    FieldSpec,
)
from owlroost.schema.utils import (
    unwrap_annotation,
    walk_model,
)

from ..specs import (
    BaseSectionConfig,
)

# =========================================================
# Section Model
# =========================================================


class SpendingPolicyConfig(
    BaseSectionConfig,
):
    """
    Spending policy configuration.
    """

    essential_spending: float = Field(
        default=0.0,
        description=("Minimum essential spending level."),
    )

    lifestyle_spending: float = Field(
        default=0.0,
        description=("Desired lifestyle spending level above essentials."),
    )

    baseline_years: int = Field(
        default=3,
        ge=0,
        description=("Number of baseline years used for spending evaluation."),
    )

    max_years_below_threshhold: int = Field(
        default=5,
        ge=0,
        description=("Maximum allowed years below spending threshold."),
    )

    max_consecutive_years_below_threshhold: int = Field(
        default=5,
        ge=0,
        description=("Maximum consecutive years allowed below threshold."),
    )


# =========================================================
# Registration
# =========================================================


def register_schema_fields(
    reg,
):
    """
    Register spending policy fields.
    """

    for name, field in walk_model(
        "",
        SpendingPolicyConfig,
    ):
        full_name = f"spending_policy.{name}"

        if full_name in reg:
            continue

        reg.register(
            FieldSpec(
                # =========================================
                # Identity
                # =========================================
                name=full_name,
                dtype=unwrap_annotation(
                    field.annotation,
                ),
                # =========================================
                # Runtime Realization
                # =========================================
                path=("spending_policy",) + tuple(name.split(".")),
                source="input",
                # =========================================
                # Ontology
                # =========================================
                owner="ROOST",
                semantic_domain="decision",
                value_origin="user-specified",
                projection_kind="canonical",
                analytic_kind="observed",
                materialization_level="case",
                node_type=(CatalogNodeType.VARIABLE),
                # =========================================
                # Documentation
                # =========================================
                description=(field.description or ""),
                # =========================================
                # Provenance
                # =========================================
                defined_in=normalize_module_path(__file__),
            )
        )
