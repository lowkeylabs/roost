# src/owlroost/schema/sections/roost_environment.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
Roost environment schema section.

Notes
-----
Defines execution environment variables
used by ROOST and downstream numerical
libraries.

These variables describe the runtime
execution environment rather than the
retirement scenario itself.

Architectural Invariant
-----------------------
This module owns:

    - section model
    - schema registration
    - ontology metadata

for the roost_environment TOML section.
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
    resolve_field_default,
    unwrap_annotation,
    walk_model,
)

from ..specs import (
    BaseSectionConfig,
)

# =========================================================
# Section Model
# =========================================================


class RoostEnvironmentConfig(
    BaseSectionConfig,
):
    """
    Runtime environment configuration.

    These settings control threading,
    parallelism, and solver execution
    environment behavior.
    """

    # -----------------------------------------------------
    # OpenMP
    # -----------------------------------------------------

    OMP_NUM_THREADS: int | None = Field(
        default=None,
        ge=1,
        description="OpenMP thread count.",
    )

    # -----------------------------------------------------
    # OpenBLAS
    # -----------------------------------------------------

    OPENBLAS_NUM_THREADS: int | None = Field(
        default=None,
        ge=1,
        description="OpenBLAS thread count.",
    )

    # -----------------------------------------------------
    # Intel MKL
    # -----------------------------------------------------

    MKL_NUM_THREADS: int | None = Field(
        default=None,
        ge=1,
        description="Intel MKL thread count.",
    )

    # -----------------------------------------------------
    # MOSEK
    # -----------------------------------------------------

    MSK_IPAR_NUM_THREADS: int | None = Field(
        default=None,
        ge=1,
        description="MOSEK thread count.",
    )


# =========================================================
# Registration
# =========================================================


def register_schema_fields(
    reg,
):
    """
    Register runtime environment fields.
    """

    for name, field in walk_model(
        "",
        RoostEnvironmentConfig,
    ):
        full_name = f"roost_environment.{name}"

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
                path=("roost_environment",) + tuple(name.split(".")),
                source="input",
                default=resolve_field_default(field),
                # =========================================
                # Ontology
                # =========================================
                owner="ROOST",
                semantic_domain="execution",
                value_origin="user-specified",
                projection_kind="canonical",
                analytic_kind="primary",
                materialization_level="case",
                node_type=CatalogNodeType.VARIABLE,
                # =========================================
                # Documentation
                # =========================================
                description=(field.description or ""),
                defined_in=normalize_module_path(__file__),
            )
        )
