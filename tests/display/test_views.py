# tests/display/test_views.py

from __future__ import annotations

from owlroost.display.registry import (
    DisplayRegistry,
)
from owlroost.display.specs import (
    DisplayField,
)
from owlroost.display.views import (
    register_case_views,
    register_run_views,
)

# =========================================================
# Helpers
# =========================================================


def build_registry():
    """
    Build minimal registry containing
    fields required by case/run views.
    """

    reg = DisplayRegistry()

    # -----------------------------------------------------
    # Identity
    # -----------------------------------------------------

    reg.register_display_field(
        DisplayField(
            field_name="case_name",
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="description",
        )
    )

    # -----------------------------------------------------
    # Runtime / execution
    # -----------------------------------------------------

    reg.register_display_field(
        DisplayField(
            field_name="roost_runtime.workers_per_run",
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="roost_runtime.trials_per_run",
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="solver_options.solver",
        )
    )

    # -----------------------------------------------------
    # Timing fields
    # -----------------------------------------------------

    timing_fields = [
        "trial.completion_rate",
        "run_timing.elapsed_seconds",
        "timing.elapsed_seconds__median",
        "timing.elapsed_seconds__mean",
        "timing.elapsed_seconds__p90",
        "run_execution.trials_per_second",
        "run_execution.parallelism",
        "run_execution.worker_utilization",
        "run_execution.trials_per_worker",
        "run_timing.latency_skew",
    ]

    for field_name in timing_fields:
        reg.register_display_field(
            DisplayField(
                field_name=field_name,
            )
        )

    return reg


# =========================================================
# Registration
# =========================================================


def test_register_case_views():
    reg = build_registry()

    register_case_views(reg)
    register_run_views(reg)

    # ----------------------------------------
    # Groups
    # ----------------------------------------

    assert reg.has_group("identity")

    assert reg.has_group("run_timing")

    # ----------------------------------------
    # Views
    # ----------------------------------------

    assert reg.has_view(
        "case",
        "basic",
    )


# =========================================================
# Identity Group
# =========================================================


def test_identity_group_entries():
    reg = build_registry()

    register_case_views(reg)

    group = reg.get_group("identity")

    assert group.entries == [
        "case_name",
    ]


def test_identity_group_description():
    reg = build_registry()

    register_case_views(reg)

    group = reg.get_group("identity")

    assert group.description == "Case identity fields."


# =========================================================
# Run Timing Group
# =========================================================


def test_run_timing_group_exists():
    reg = build_registry()

    register_case_views(reg)
    register_run_views(reg)

    assert reg.has_group(
        "run_timing",
    )


def test_run_timing_group_contains_workers():
    reg = build_registry()

    register_case_views(reg)
    register_run_views(reg)

    group = reg.get_group(
        "run_timing",
    )

    assert "roost_runtime.workers_per_run" in group.entries


def test_run_timing_group_description():
    reg = build_registry()

    register_case_views(reg)
    register_run_views(reg)

    group = reg.get_group(
        "run_timing",
    )

    assert isinstance(
        group.description,
        str,
    )

    assert len(group.description) > 0


# =========================================================
# View
# =========================================================


def test_case_basic_view_exists():
    reg = build_registry()

    register_case_views(reg)

    view = reg.get_view(
        "case",
        "basic",
    )

    assert view.level == "case"

    assert view.name == "basic"


# =========================================================
# Duplicate Registration
# =========================================================


def test_register_case_views_twice_raises():
    reg = build_registry()

    register_case_views(reg)

    try:
        register_case_views(reg)

        raised = False

    except ValueError:
        raised = True

    assert raised


def test_register_run_views_twice_raises():
    reg = build_registry()

    register_run_views(reg)

    try:
        register_run_views(reg)

        raised = False

    except ValueError:
        raised = True

    assert raised


# =========================================================
# Missing Field Validation
# =========================================================


def test_missing_field_validation_fails():
    reg = DisplayRegistry()

    # ----------------------------------------
    # Deliberately incomplete registry
    # ----------------------------------------

    reg.register_display_field(
        DisplayField(
            field_name="case_name",
        )
    )

    register_case_views(reg)

    try:
        reg.validate()

        raised = False

    except ValueError:
        raised = True

    assert raised
