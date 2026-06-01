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
"""

from __future__ import annotations

from owlroost.display.specs import (
    DisplayField,
)


def register_display_fields(
    reg,
):
    # =====================================================
    # Constant scalar
    # =====================================================

    reg.register_display_field(
        DisplayField.field(
            "testing.scalar",
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
            display_fn=lambda row: None,
            owner="ROOST",
            semantic_domain="execution",
            value_origin="roost-computed",
            projection_kind="synthetic",
            description=("Deterministic ontology fixture."),
        )
    )
