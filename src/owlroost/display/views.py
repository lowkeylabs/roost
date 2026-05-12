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


def register_run_views(reg):
    # =====================================================
    # Identity
    # =====================================================

    reg.register_group(
        DisplayGroup(
            key="run_identity",
            entries=[
                "case_name",
                "display.current_ages",
            ],
            description="Run identity.",
        )
    )

    # =====================================================
    # Planning
    # =====================================================

    reg.register_group(
        DisplayGroup(
            key="run_planning",
            entries=[
                "optimization_parameters.objective",
                "roost.trials_per_run",
                "rates_selection.method",
            ],
            description="Planning configuration.",
        )
    )

    # =====================================================
    # Execution
    # =====================================================

    reg.register_group(
        DisplayGroup(
            key="run_execution",
            entries=[
                "trial.completed",
                "trial.pending",
                "trial.completion_rate",
            ],
            description="Run execution summary.",
        )
    )

    # =====================================================
    # Outcomes
    # =====================================================

    reg.register_group(
        DisplayGroup(
            key="run_outcomes",
            entries=[
                # -----------------------------------------
                # Spending
                # -----------------------------------------
                "financial.spending.year0.today__median",
                "financial.spending.total.today__median",
                # -----------------------------------------
                # Bequest
                # -----------------------------------------
                "financial.bequest.total.today__median",
                # -----------------------------------------
                # Timing
                # -----------------------------------------
                "timing.elapsed_seconds__median",
            ],
            description="Aggregated financial outcomes.",
        )
    )

    # =====================================================
    # Basic Run View
    # =====================================================

    reg.register_view(
        ViewSpec(
            level="run",
            name="basic",
            entries=[
                ("group", "run_identity"),
                ("group", "run_planning"),
                ("group", "run_execution"),
                ("group", "run_outcomes"),
            ],
            description="Default run results view.",
        )
    )
