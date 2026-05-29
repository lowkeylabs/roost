# src/owlroost/display/fields/runtime.py

from __future__ import annotations

from owlroost.display.specs import (
    DisplayField,
    DisplayProfile,
)

# =========================================================
# Registration
# =========================================================


def register_display_fields(
    reg,
):
    """
    Register operational runtime and execution fields.

    These fields focus on:
        - execution state
        - trial completion
        - operational runtime progress
        - run completion summaries

    This module intentionally excludes:
        - scaling diagnostics
        - throughput analysis
        - methodology configuration
        - provenance metadata
    """

    # =====================================================
    # Completed Trials
    # =====================================================

    reg.register_display_field(
        DisplayField(
            field_name="trial.completed",
            description=("Number of completed trials."),
            profiles={
                "table": DisplayProfile(
                    label="Done",
                    content_align="right",
                ),
                "pivot": DisplayProfile(
                    label="Completed",
                    content_align="right",
                ),
            },
        )
    )

    # =====================================================
    # Pending Trials
    # =====================================================

    reg.register_display_field(
        DisplayField(
            field_name="trial.pending",
            description=("Number of pending trials."),
            profiles={
                "table": DisplayProfile(
                    label="Pending",
                    content_align="right",
                ),
                "pivot": DisplayProfile(
                    label="Pending",
                    content_align="right",
                ),
            },
        )
    )

    # =====================================================
    # Total Trials
    # =====================================================

    reg.register_display_field(
        DisplayField(
            field_name="trial.total",
            description=("Total configured trials."),
            profiles={
                "table": DisplayProfile(
                    label="Trials",
                    content_align="right",
                ),
                "pivot": DisplayProfile(
                    label="Total Trials",
                    content_align="right",
                ),
            },
        )
    )

    # =====================================================
    # Trial Completion Rate
    # =====================================================

    reg.register_display_field(
        DisplayField(
            field_name="trial.completion_rate",
            description=("Fraction of completed trials."),
            profiles={
                "table": DisplayProfile(
                    label="Complete\n%",
                    fmt="percent",
                    content_align="right",
                ),
                "pivot": DisplayProfile(
                    label="Completion Rate",
                    fmt="percent",
                    content_align="right",
                ),
            },
        )
    )

    # =====================================================
    # Completion Ratio
    # =====================================================

    reg.register_display_field(
        DisplayField(
            field_name="completion_ratio",
            display_fn=completion_ratio_display,
            description=("Completed trials relative to configured trials per run."),
            profiles={
                "table": DisplayProfile(
                    label="Trials",
                    content_align="center",
                ),
                "pivot": DisplayProfile(
                    label="Completion Ratio",
                    content_align="center",
                ),
            },
        )
    )


# =========================================================
# Display Functions
# =========================================================


def completion_ratio_display(
    row,
):
    """
    Return compact completion ratio.

    Examples:

        0/50
        17/50
        50/50
    """

    try:
        completed = row.get(
            "_metrics",
            {},
        ).get("trial.completed")

        total = (
            row.get(
                "_inputs",
                {},
            )
            .get(
                "roost_runtime",
                {},
            )
            .get("trials_per_run")
        )

        if completed is None or total is None:
            return "."

        return f"{completed}/{total}"

    except Exception:
        return "."
