# src/owlroost/display/fields/00_examples.py

"""
Display field examples.

Notes
-----
This module demonstrates supported
DisplayField declaration patterns.

All example fields live within the
example.* namespace.

Examples may reference stable schema
and metric ontology concepts, but must
not override production display fields.
"""

from __future__ import annotations

from owlroost.core.utils import normalize_module_path
from owlroost.display.specs import (
    DisplayField,
    DisplayProfile,
)

EXAMPLE_ONTOLOGY = dict(
    owner="ROOST",
    semantic_domain="execution",
    value_origin="roost-computed",
    projection_kind="synthetic",
    analytic_kind="observed",
    materialization_level="case",
    node_type="variable",
    defined_in=normalize_module_path(__file__),
)


def register_display_fields(
    reg,
):
    # =====================================================
    # Schema-backed overlay example
    # =====================================================

    reg.register_display_field(
        DisplayField.field(
            "example.bequest_overlay",
            **EXAMPLE_ONTOLOGY,
            description=("Example field modeled after solver_options.bequest."),
            profiles={
                "table": DisplayProfile(
                    label="Example\nBequest",
                    fmt="currency_short",
                    content_align="right",
                ),
            },
        )
    )

    # =====================================================
    # Metric-backed overlay example
    # =====================================================

    reg.register_display_field(
        DisplayField.field(
            "example.runtime_metric",
            **EXAMPLE_ONTOLOGY,
            description=("Example field modeled after elapsed runtime."),
            derived_from=[
                "timing.elapsed_seconds__median",
            ],
            profiles={
                "table": DisplayProfile(
                    label="Runtime",
                    fmt="seconds",
                    content_align="right",
                ),
            },
        )
    )

    # =====================================================
    # Simple synthetic field
    # =====================================================

    reg.register_display_field(
        DisplayField.field(
            "example.synthetic",
            display_fn=lambda row: 42,
            owner="ROOST",
            semantic_domain="execution",
            value_origin="roost-computed",
            projection_kind="synthetic",
            analytic_kind="observed",
            materialization_level="case",
            node_type="variable",
            defined_in=normalize_module_path(__file__),
            description=("Simple synthetic example."),
        )
    )

    # =====================================================
    # Compositional field
    # =====================================================

    reg.register_display_field(
        DisplayField.field(
            "example.composed",
            display_fn=lambda row: 100,
            owner="ROOST",
            semantic_domain="execution",
            value_origin="roost-computed",
            projection_kind="synthetic",
            analytic_kind="observed",
            materialization_level="case",
            node_type="variable",
            defined_in=normalize_module_path(__file__),
            derived_from=[
                "example.synthetic",
                "example.runtime_metric",
            ],
            description=("Compositional synthetic example."),
            profiles={
                "table": DisplayProfile(
                    label="Composed",
                    fmt="integer",
                    content_align="right",
                ),
            },
        )
    )

    # =====================================================
    # Hidden helper field
    # =====================================================

    reg.register_display_field(
        DisplayField.field(
            "example.hidden",
            display_fn=lambda row: 0,
            owner="ROOST",
            semantic_domain="execution",
            value_origin="roost-computed",
            projection_kind="synthetic",
            analytic_kind="observed",
            materialization_level="case",
            node_type="variable",
            description=("Hidden helper example."),
            defined_in=normalize_module_path(__file__),
            profiles={
                "table": DisplayProfile(
                    visible=False,
                ),
            },
        )
    )

    # =====================================================
    # Explicit ontology example
    # =====================================================

    reg.register_display_field(
        DisplayField.field(
            "example.semantic",
            display_fn=lambda row: None,
            owner="ROOST",
            semantic_domain="execution",
            value_origin="roost-computed",
            projection_kind="synthetic",
            analytic_kind="observed",
            materialization_level="case",
            node_type="variable",
            defined_in=normalize_module_path(__file__),
            description=("Example carrying explicit ontology."),
        )
    )

    # =====================================================
    # Multiple profile example
    # =====================================================

    reg.register_display_field(
        DisplayField.field(
            "example.multiple_profiles",
            display_fn=lambda row: "X",
            owner="ROOST",
            semantic_domain="execution",
            value_origin="roost-computed",
            projection_kind="synthetic",
            analytic_kind="observed",
            materialization_level="case",
            node_type="variable",
            defined_in=normalize_module_path(__file__),
            profiles={
                "table": DisplayProfile(
                    label="Table",
                ),
                "pivot": DisplayProfile(
                    label="Pivot",
                ),
                "export": DisplayProfile(
                    label="Export",
                ),
            },
        )
    )

    # =====================================================
    # Expansion example
    # =====================================================

    reg.register_display_field(
        DisplayField.field(
            "example.expansion",
            display_fn=lambda row: None,
            owner="ROOST",
            semantic_domain="execution",
            value_origin="roost-computed",
            projection_kind="synthetic",
            analytic_kind="observed",
            materialization_level="case",
            node_type="variable",
            defined_in=normalize_module_path(__file__),
            expands_to=[
                "example.synthetic",
                "example.composed",
            ],
            description=("Example expansion relationship."),
        )
    )
