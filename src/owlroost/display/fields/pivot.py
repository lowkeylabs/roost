# src/owlroost/display/fields/pivot.py

"""
Pivot display fields.

Notes
-----
Synthetic display fields used by
pivot_table().

These fields provide catalog identity
and presentation metadata for the
synthetic columns created during
pivot rendering.
"""

from __future__ import annotations

from owlroost.core.utils import normalize_module_path
from owlroost.display.specs import (
    DisplayField,
    DisplayProfile,
)

# =========================================================
# Pivot Ontology
# =========================================================

PIVOT_ONTOLOGY = dict(
    owner="ROOST",
    semantic_domain="design",
    value_origin="roost-computed",
    projection_kind="synthetic",
    analytic_kind="observed",
    materialization_level="display",
    node_type="variable",
    defined_in=normalize_module_path(__file__),
)


# =========================================================
# Registration
# =========================================================


def register_display_fields(
    reg,
):
    """
    Register pivot display fields.
    """

    # =====================================================
    # Metric Column
    # =====================================================

    reg.register_display_field(
        DisplayField.field(
            "pivot_metric",
            description=("Synthetic pivot metric label column."),
            profiles={
                "table": DisplayProfile(
                    label="Metric",
                    width=20,
                    wrap=True,
                ),
            },
            **PIVOT_ONTOLOGY,
        )
    )

    # =====================================================
    # Value Column
    # =====================================================

    reg.register_display_field(
        DisplayField.field(
            "pivot_value",
            description=("Synthetic pivot value column."),
            profiles={
                "table": DisplayProfile(
                    label="Value",
                    width=50,
                    wrap=True,
                ),
            },
            **PIVOT_ONTOLOGY,
        )
    )

    # =====================================================
    # Explanation Column
    # =====================================================

    reg.register_display_field(
        DisplayField.field(
            "pivot_explanation",
            description=("Synthetic pivot explanation column."),
            profiles={
                "table": DisplayProfile(
                    label="Explanation",
                    width=50,
                    wrap=True,
                ),
            },
            **PIVOT_ONTOLOGY,
        )
    )
