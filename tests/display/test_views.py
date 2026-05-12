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
)

# =========================================================
# Helpers
# =========================================================


def build_registry():
    """
    Build minimal registry containing
    fields required by case views.
    """

    reg = DisplayRegistry()

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

    reg.register_display_field(
        DisplayField(
            field_name="runtime.trial_jobs",
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="runtime.run_jobs",
        )
    )

    return reg


# =========================================================
# Registration
# =========================================================


def test_register_case_views():
    reg = build_registry()

    register_case_views(reg)

    # ----------------------------------------
    # Groups
    # ----------------------------------------
    assert reg.has_group("identity")

    assert reg.has_group("runtime")

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
# Runtime Group
# =========================================================


def test_runtime_group_entries():
    reg = build_registry()

    register_case_views(reg)

    group = reg.get_group("runtime")

    assert group.entries == [
        "runtime.trial_jobs",
        "runtime.run_jobs",
    ]


def test_runtime_group_description():
    reg = build_registry()

    register_case_views(reg)

    group = reg.get_group("runtime")

    assert group.description == "Runtime configuration."


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
