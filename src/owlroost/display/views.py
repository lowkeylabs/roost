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
            key="planning",
            entries=[
                "optimization_parameters.objective",
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
                {"field": "compact_id", "show_if": ["is_table"]},
                {"field": "case_id", "show_if": ["is_pivot"]},
                {"field": "experiment_id", "show_if": ["is_pivot"]},
                {"field": "run_id", "show_if": ["is_pivot"]},
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
                {"field": "completion_ratio", "show_if": ["is_table"]},
                {"field": "trial.completed", "show_if": ["is_pivot"]},
                {"field": "roost_runtime.trials_per_run", "show_if": ["is_pivot"]},
                {"field": "trial.completion_rate", "show_if": ["is_pivot"]},
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

    reg.register_group(
        DisplayGroup(
            key="run_timing",
            entries=[
                # -----------------------------------------
                # Execution configuration
                # -----------------------------------------
                "solver_options.solver",
                "roost_runtime.workers_per_run",
                "roost_runtime.math_library_threads",
                "runtime_environment.MSK_IPAR_NUM_THREADS",
                # -----------------------------------------
                # Completion
                # -----------------------------------------
                "trial.completion_rate",
                # -----------------------------------------
                # Run wall-clock timing
                # -----------------------------------------
                "run_timing.elapsed_seconds",
                # -----------------------------------------
                # Trial timing aggregates
                # -----------------------------------------
                "timing.elapsed_seconds__median",
                "timing.elapsed_seconds__mean",
                "timing.elapsed_seconds__p90",
                # -----------------------------------------
                # Derived execution metrics
                # -----------------------------------------
                "run_execution.trials_per_second",
                "run_execution.concurrency_equivalent",
                "run_execution.worker_utilization",
                # -----------------------------------------
                # Derived timing diagnostics
                # -----------------------------------------
                "run_timing.trial_latency_skew",
            ],
            description=("Run-level execution, throughput, " "and timing diagnostics."),
        )
    )

    # =====================================================
    # Overrides
    # =====================================================

    reg.register_group(
        DisplayGroup(
            key="run_overrides",
            entries=[
                "run_execution.run_specific_overrides",
                "run_execution.common_overrides",
            ],
            description="Run comparison overrides.",
        )
    )

    # =====================================================
    # Basic Run View
    # =====================================================

    reg.register_view(
        ViewSpec(
            level="run",
            name="results",
            entries=[
                ("group", "run_identity"),
                ("group", "run_execution"),
                ("group", "run_planning"),
                ("group", "run_outcomes"),
            ],
            description="Default run results view.",
        )
    )

    reg.register_view(
        ViewSpec(
            level="run",
            name="timing",
            entries=[
                ("group", "run_identity"),
                ("group", "run_timing"),
            ],
            description="Default run timing.",
        )
    )

    reg.register_view(
        ViewSpec(
            level="run",
            name="run",
            entries=[
                ("group", "run_identity"),
                ("group", "run_execution"),
                ("group", "run_overrides"),
            ],
            description="Compact run execution view.",
        )
    )
