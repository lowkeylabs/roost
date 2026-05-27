# src/owlroost/display/groups.py

from __future__ import annotations

from owlroost.display.specs import (
    DisplayGroup,
)


def register_display_groups(
    reg,
):
    """
    Register all display groups.

    Groups are semantic reusable collections of fields.

    Views compose groups together into
    presentation-oriented layouts.
    """

    # =====================================================
    # Identity
    # =====================================================

    reg.register_group(
        DisplayGroup(
            key="identity",
            entries=[
                "case_name",
                {"field": "compact_id", "show_if": ["is_table"]},
                {"field": "case_id", "show_if": ["is_pivot"]},
                {"field": "session_id", "show_if": ["is_pivot"]},
                {"field": "run_id", "show_if": ["is_pivot"]},
            ],
            description="Operational identity fields.",
        )
    )

    # =====================================================
    # Planning
    # =====================================================

    reg.register_group(
        DisplayGroup(
            key="planning",
            entries=[
                "display.optimization_goal",
                "rates_selection.method",
                "display.rates_window",
                {"field": "optimization_parameters.objective", "show_if": ["is_pivot"]},
                {"field": "solver_options.netSpending", "show_if": ["is_pivot"]},
                {"field": "solver_options.bequest", "show_if": ["is_pivot"]},
            ],
            description="Planning configuration.",
        )
    )

    # =====================================================
    # Execution
    # =====================================================

    reg.register_group(
        DisplayGroup(
            key="execution",
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
            key="outcomes",
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
    # Timing
    # =====================================================

    reg.register_group(
        DisplayGroup(
            key="timing",
            entries=[
                # -----------------------------------------
                # Execution configuration
                # -----------------------------------------
                "solver_options.solver",
                "roost_runtime.workers_per_run",
                "compact_threads",
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
            key="overrides",
            entries=[
                "run_execution.run_specific_overrides",
                "run_execution.common_overrides",
            ],
            description="Run comparison overrides.",
        )
    )

    # =====================================================
    # Provenance
    # =====================================================

    reg.register_group(
        DisplayGroup(
            key="provenance",
            entries=[
                "case_name",
                "compact_id",
                "session.date",
                "session.time",
            ],
            description="Operational provenance identity.",
        )
    )

    # =====================================================
    # Inventory
    # =====================================================

    reg.register_group(
        DisplayGroup(
            key="inventory",
            entries=[
                "session.count",
                "run.count",
                "trial.total",
                "trial.completed",
                "trial.pending",
            ],
            description="Operational execution inventory.",
        )
    )

    # =====================================================
    # Demographics
    # =====================================================

    reg.register_group(
        DisplayGroup(
            key="top_level",
            entries=[
                "display.current_ages",
                "display.life_expectancy",
                "display.net_worth",
                "display.total_assets",
                "display.total_liabilities",
                "display.fixed_income",
            ],
            description="Top-level household metrics.",
        )
    )

    # =====================================================
    # Balances
    # =====================================================

    reg.register_group(
        DisplayGroup(
            key="balances",
            entries=[
                # -----------------------------------------
                # Household Scale
                # -----------------------------------------
                "display.net_worth",
                "display.total_assets",
                "display.total_liabilities",
                # -----------------------------------------
                # Retirement Portfolio
                # -----------------------------------------
                "display.total_savings",
                "display.taxable_savings",
                "display.tax_deferred_savings",
                "display.tax_free_savings",
                # -----------------------------------------
                # Household Financial Profile Presence
                # -----------------------------------------
                "display.has_hfp_file",
                "display.has_fixed_assets",
                "display.has_debts",
                # -----------------------------------------
                # Household Balance Sheet
                # -----------------------------------------
                "display.net_hfp_assets",
                "display.fixed_assets",
                "display.residence_value",
                "display.mortgage_debt",
                # -----------------------------------------
                # Guaranteed Income
                # -----------------------------------------
                "fixed_income.social_security_pia_amounts",
                "display.social_security_income",
                "display.pension_income",
                "display.fixed_income",
            ],
            description=(
                "Household financial summary including "
                "demographics, retirement savings structure, "
                "household financial profile assets and debts, "
                "residence value, mortgage debt, total balance "
                "sheet assets, and guaranteed retirement income."
            ),
        )
    )
