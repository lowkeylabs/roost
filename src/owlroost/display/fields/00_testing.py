# src/owlroost/display/fields/00_testing.py

"""
Display testing fixtures.

Notes
-----
This module provides deterministic,
stable display fields intended for
automated testing.

All testing fixtures live within the
testing.* namespace.

The goal is predictability rather than
demonstrating architectural patterns.

Architectural Invariant
-----------------------
Testing fields participate in catalog
synthesis exactly like production fields.

Therefore every testing semantic entity
must declare complete ontology metadata.
"""

from __future__ import annotations

from owlroost.display.specs import (
    DisplayField,
)

# =========================================================
# Shared Ontology
# =========================================================

TEST_ONTOLOGY = dict(
    owner="ROOST",
    semantic_domain="execution",
    value_origin="roost-computed",
    projection_kind="synthetic",
    analytic_kind="observed",
    materialization_level="case",
    node_type="variable",
)

# =========================================================
# Registration
# =========================================================


def register_display_fields(
    reg,
):
    # =====================================================
    # Constant scalar
    # =====================================================

    reg.register_display_field(
        DisplayField.field(
            "testing.scalar",
            **TEST_ONTOLOGY,
            display_fn=lambda row: 123,
            description=("Deterministic scalar."),
        )
    )

    # =====================================================
    # Constant string
    # =====================================================

    reg.register_display_field(
        DisplayField.field(
            "testing.string",
            **TEST_ONTOLOGY,
            display_fn=lambda row: "TEST",
            description=("Deterministic string."),
        )
    )

    # =====================================================
    # Constant boolean
    # =====================================================

    reg.register_display_field(
        DisplayField.field(
            "testing.boolean",
            **TEST_ONTOLOGY,
            display_fn=lambda row: True,
            description=("Deterministic boolean."),
        )
    )

    # =====================================================
    # Synthetic composition
    # =====================================================

    reg.register_display_field(
        DisplayField.field(
            "testing.composed",
            **TEST_ONTOLOGY,
            display_fn=lambda row: 456,
            derived_from=[
                "testing.scalar",
                "testing.boolean",
            ],
            description=("Deterministic composed fixture."),
        )
    )

    # =====================================================
    # Explicit ontology fixture
    # =====================================================

    reg.register_display_field(
        DisplayField.field(
            "testing.semantic",
            **TEST_ONTOLOGY,
            display_fn=lambda row: None,
            description=("Deterministic ontology fixture."),
        )
    )
