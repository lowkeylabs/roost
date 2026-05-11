# src/owlroost/display/views.py

from __future__ import annotations

from owlroost.display.specs import (
    DisplayGroup,
    ViewSpec,
)


def register_case_views(reg):
    """
    Register initial case-layer views.
    """

    # =====================================================
    # Identity
    # =====================================================

    reg.register_group(
        DisplayGroup(
            key="identity",
            entries=[
                "case_name",
            ],
            description="Case identity fields.",
        )
    )

    # =====================================================
    # Runtime
    # =====================================================

    reg.register_group(
        DisplayGroup(
            key="runtime",
            entries=[
                "runtime.trial_jobs",
                "runtime.run_jobs",
            ],
            description="Runtime configuration.",
        )
    )

    reg.register_group(
        DisplayGroup(
            key="planning",
            entries=[
                "optimization_parameters.objective",
                "roost.trials_per_run",
                "rates_selection.method",
            ],
            description="Planning configuration.",
        )
    )

    # =====================================================
    # Build View
    # =====================================================

    reg.register_view(
        ViewSpec(
            level="case",
            name="basic",
            entries=[
                ("group", "identity"),
                "display.current_ages",
                ("group", "planning"),
            ],
            description="Default build view.",
        )
    )
