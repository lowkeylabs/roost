# src/owlroost/schema/owl/pydantic.py
#
# Copyright (c) 2026 John Leonard
# All rights reserved.
# SPDX-License-Identifier: LicenseRef-OwlRoost-Proprietary
# See LICENSE file in repository root.

"""
OWL schema ontology loader.

Notes
-----
Loads canonical OWL configuration ontology
from the OWL Pydantic schema.

Responsibilities
----------------
    - discover OWL input variables
    - synthesize FieldSpec definitions
    - attach generated OWL documentation
    - expand special OWL sections that are
      represented as Dict[str, Any] in the
      public schema

This module is the authoritative source
for OWL input ontology.
"""

from __future__ import annotations

from owlplanner.config.schema import (
    CaseConfig,
    SolverOptions,
)

from owlroost.catalog.ontology import (
    CatalogNodeType,
)
from owlroost.core.utils import normalize_module_path

from ..generated.owl_parameter_docs import (
    OWL_PARAMETER_DOCS,
)
from ..registry import (
    FieldSpec,
)
from ..utils import (
    unwrap_annotation,
    walk_model,
)

# =========================================================
# OWL Schema Expansions
# =========================================================

EXPANSIONS = {
    "solver_options": SolverOptions,
}

# =========================================================
# Registration
# =========================================================


def register_schema_fields(
    reg,
):
    """
    Register canonical OWL schema fields.
    """

    for name, field in walk_model(
        "",
        CaseConfig,
        expansions=EXPANSIONS,
    ):
        doc = OWL_PARAMETER_DOCS.get(
            name.split(".")[-1],
            {},
        )

        reg.register(
            FieldSpec(
                # =========================================
                # Identity
                # =========================================
                name=name,
                # =========================================
                # Typing
                # =========================================
                dtype=unwrap_annotation(
                    field.annotation,
                ),
                # =========================================
                # Runtime Realization
                # =========================================
                path=tuple(name.split(".")),
                source="input",
                # =========================================
                # Ontology
                # =========================================
                owner="OWL",
                semantic_domain="decision",
                value_origin="user-specified",
                projection_kind="canonical",
                analytic_kind="observed",
                materialization_level="case",
                node_type=(CatalogNodeType.VARIABLE),
                # =========================================
                # Documentation
                # =========================================
                description=(doc.get("description") or field.description or ""),
                units=doc.get("units"),
                # =========================================
                # Provenance
                # =========================================
                defined_in=normalize_module_path(__file__),
            )
        )
