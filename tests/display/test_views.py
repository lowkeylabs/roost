# tests/display/test_views.py

from __future__ import annotations

import pytest

from owlroost.display.groups import (
    register_display_groups,
)
from owlroost.display.registry import (
    DisplayRegistry,
)
from owlroost.display.specs import (
    DisplayField,
)
from owlroost.display.views import (
    register_display_views,
)

# =========================================================
# Helpers
# =========================================================


def build_registry():
    """
    Build minimal registry capable of validating
    current display groups + views.
    """

    reg = DisplayRegistry()

    # =====================================================
    # Identity
    # =====================================================

    identity_fields = [
        "case_name",
        "compact_id",
        "case_id",
        "session_id",
        "run_id",
    ]

    # =====================================================
    # Planning
    # =====================================================

    planning_fields = [
        "optimization_parameters.objective",
        "rates_selection.method",
        "display.optimization_goal",
        "display.rates_window",
    ]

    # =====================================================
    # Execution
    # =====================================================

    execution_fields = [
        "completion_ratio",
        "trial.completed",
        "roost_runtime.trials_per_run",
        "trial.completion_rate",
    ]

    # =====================================================
    # Outcomes
    # =====================================================

    outcome_fields = [
        "financial.spending.year0.today__median",
        "financial.spending.total.today__median",
        "financial.bequest.total.today__median",
        "timing.elapsed_seconds__median",
    ]

    # =====================================================
    # Timing
    # =====================================================

    timing_fields = [
        "solver_options.solver",
        "roost_runtime.workers_per_run",
        "compact_threads",
        "run_timing.elapsed_seconds",
        "timing.elapsed_seconds__mean",
        "timing.elapsed_seconds__p90",
        "run_execution.trials_per_second",
        "run_execution.concurrency_equivalent",
        "run_execution.worker_utilization",
        "run_timing.trial_latency_skew",
    ]

    # =====================================================
    # Overrides
    # =====================================================

    override_fields = [
        "run_execution.run_specific_overrides",
        "run_execution.common_overrides",
    ]

    # =====================================================
    # Provenance
    # =====================================================

    provenance_fields = [
        "session.date",
        "session.time",
    ]

    # =====================================================
    # Inventory
    # =====================================================

    inventory_fields = [
        "session.count",
        "run.count",
        "trial.total",
        "trial.pending",
    ]

    # =====================================================
    # Balances
    # =====================================================

    balance_fields = [
        "display.current_ages",
        "display.life_expectancy",
        "display.net_worth",
        "display.total_assets",
        "display.total_savings",
        "display.taxable_savings",
        "display.tax_deferred_savings",
        "display.tax_free_savings",
        "display.has_hfp_file",
        "display.has_fixed_assets",
        "display.has_debts",
        "display.net_hfp_assets",
        "display.fixed_assets",
        "display.total_liabilities",
        "display.residence_value",
        "display.mortgage_debt",
        "display.social_security_income",
        "display.pension_income",
        "display.fixed_income",
        "fixed_income.social_security_pia_amounts",
    ]

    # =====================================================
    # Register all fields
    # =====================================================

    all_fields = (
        identity_fields
        + planning_fields
        + execution_fields
        + outcome_fields
        + timing_fields
        + override_fields
        + provenance_fields
        + inventory_fields
        + balance_fields
    )

    for field_name in all_fields:
        reg.register_display_field(
            DisplayField(
                field_name=field_name,
            )
        )

    return reg


# =========================================================
# Registration
# =========================================================


def test_register_display_groups():
    reg = build_registry()

    register_display_groups(reg)

    assert reg.has_group("identity")
    assert reg.has_group("planning")
    assert reg.has_group("execution")
    assert reg.has_group("outcomes")
    assert reg.has_group("timing")
    assert reg.has_group("overrides")
    assert reg.has_group("provenance")
    assert reg.has_group("inventory")
    assert reg.has_group("balances")


def test_register_display_views():
    reg = build_registry()

    register_display_groups(reg)
    register_display_views(reg)

    assert reg.has_view("case", "cases")
    assert reg.has_view("case", "results")
    assert reg.has_view("case", "balances")

    assert reg.has_view("session", "results")

    assert reg.has_view("run", "results")
    assert reg.has_view("run", "timing")
    assert reg.has_view("run", "run")
    assert reg.has_view("run", "balances")


# =========================================================
# Identity Group
# =========================================================


def test_identity_group_entries():
    reg = build_registry()

    register_display_groups(reg)

    group = reg.get_group("identity")

    assert group.entries == [
        "case_name",
        {"field": "compact_id", "show_if": ["is_table"]},
        {"field": "case_id", "show_if": ["is_pivot"]},
        {"field": "session_id", "show_if": ["is_pivot"]},
        {"field": "run_id", "show_if": ["is_pivot"]},
    ]


def test_identity_group_description():
    reg = build_registry()

    register_display_groups(reg)

    group = reg.get_group("identity")

    assert isinstance(group.description, str)

    assert len(group.description) > 0


# =========================================================
# Timing Group
# =========================================================


def test_timing_group_exists():
    reg = build_registry()

    register_display_groups(reg)

    assert reg.has_group("timing")


def test_timing_group_contains_workers():
    reg = build_registry()

    register_display_groups(reg)

    group = reg.get_group("timing")

    assert "roost_runtime.workers_per_run" in group.entries


def test_timing_group_description():
    reg = build_registry()

    register_display_groups(reg)

    group = reg.get_group("timing")

    assert isinstance(group.description, str)

    assert len(group.description) > 0


# =========================================================
# View Definitions
# =========================================================


def test_case_basic_view():
    reg = build_registry()

    register_display_groups(reg)
    register_display_views(reg)

    view = reg.get_view(
        "case",
        "cases",
    )

    assert view.level == "case"

    assert view.name == "cases"

    assert ("group", "top_level") in view.entries

    # assert ("group", "planning") in view.entries


def test_run_results_view():
    reg = build_registry()

    register_display_groups(reg)
    register_display_views(reg)

    view = reg.get_view(
        "run",
        "results",
    )

    assert view.level == "run"

    assert view.name == "results"

    assert ("group", "execution") in view.entries

    assert ("group", "outcomes") in view.entries


# =========================================================
# Duplicate Registration
# =========================================================


def test_register_groups_twice_raises():
    reg = build_registry()

    register_display_groups(reg)

    with pytest.raises(ValueError):
        register_display_groups(reg)


def test_register_views_twice_raises():
    reg = build_registry()

    register_display_groups(reg)
    register_display_views(reg)

    with pytest.raises(ValueError):
        register_display_views(reg)


# =========================================================
# Validation
# =========================================================


def test_registry_validation_passes():
    reg = build_registry()

    register_display_groups(reg)
    register_display_views(reg)

    reg.validate()


def test_missing_field_validation_fails():
    reg = DisplayRegistry()

    reg.register_display_field(
        DisplayField(
            field_name="case_name",
        )
    )

    register_display_groups(reg)
    register_display_views(reg)

    with pytest.raises(ValueError):
        reg.validate()
