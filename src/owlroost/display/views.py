# src/owlroost/display/views.py

from __future__ import annotations

from owlroost.display.specs import (
    ViewSpec,
)


def register_display_views(
    reg,
):
    """
    Register all display views.

    Views are declarative layouts composed
    from reusable display groups and fields.

    Views are uniquely identified by:

        (level, name)

    Examples:

        ("case", "basic")
        ("run", "results")
        ("session", "results")
    """

    # =====================================================
    # CASE VIEWS
    # =====================================================

    reg.register_view(
        ViewSpec(
            level="case",
            name="cases",
            entries=[
                ("case_name"),
                ("group", "top_level"),
                # ("group", "planning"),
            ],
            description=(
                "Default case dashboard showing "
                "household demographics, high-level "
                "financial structure, and planning "
                "configuration."
            ),
        )
    )

    reg.register_view(
        ViewSpec(
            level="case",
            name="build",
            entries=[
                ("group", "identity"),
                # ("group", "balances"),
                ("group", "planning"),
            ],
            description=(
                "Default case dashboard showing "
                "household demographics, high-level "
                "financial structure, and planning "
                "configuration."
            ),
        )
    )

    reg.register_view(
        ViewSpec(
            level="case",
            name="results",
            entries=[
                ("group", "identity"),
                ("group", "inventory"),
            ],
            description=(
                "Operational case summary showing "
                "execution provenance and aggregate "
                "run/trial inventory."
            ),
        )
    )

    reg.register_view(
        ViewSpec(
            level="case",
            name="balances",
            entries=[
                ("group", "identity"),
                ("group", "balances"),
            ],
            description=(
                "Household balance sheet summary "
                "including retirement savings structure, "
                "fixed assets, debts, net worth, "
                "and guaranteed retirement income."
            ),
        )
    )

    # =====================================================
    # SESSION VIEWS
    # =====================================================

    reg.register_view(
        ViewSpec(
            level="session",
            name="results",
            entries=[
                ("group", "provenance"),
                ("group", "inventory"),
            ],
            description=(
                "Operational session provenance summary "
                "showing execution inventory and "
                "completion status."
            ),
        )
    )

    # =====================================================
    # RUN VIEWS
    # =====================================================

    reg.register_view(
        ViewSpec(
            level="run",
            name="results",
            entries=[
                ("group", "identity"),
                ("group", "execution"),
                ("group", "planning"),
                ("group", "outcomes"),
            ],
            description="Default run results view.",
        )
    )

    reg.register_view(
        ViewSpec(
            level="run",
            name="timing",
            entries=[
                ("group", "identity"),
                ("group", "timing"),
            ],
            description="Default run timing.",
        )
    )

    reg.register_view(
        ViewSpec(
            level="run",
            name="run",
            entries=[
                ("group", "identity"),
                ("group", "execution"),
                ("group", "overrides"),
            ],
            description="Compact run execution view.",
        )
    )

    reg.register_view(
        ViewSpec(
            level="run",
            name="balances",
            entries=[
                ("group", "identity"),
                ("group", "balances"),
            ],
            description=(
                "Household balance sheet summary "
                "including retirement savings structure, "
                "fixed assets, debts, net worth, "
                "and guaranteed retirement income."
            ),
        )
    )
