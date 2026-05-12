# src/owlroost/display/overrides.py

from __future__ import annotations

from datetime import date

from owlroost.display.specs import (
    DisplayField,
    DisplayProfile,
)


def apply_display_overrides(
    reg,
):
    """
    Apply curated display overrides.

    Current implementation intentionally minimal.

    This subsystem will eventually support:
    - custom labels
    - custom formats
    - explanations
    - visibility rules
    - mode-specific overrides

    For now, schema-generated defaults are used.
    """

    # =====================================================
    # Planning
    # =====================================================

    reg.register_display_field(
        DisplayField(
            field_name="roost.trials_per_run",
            profiles={
                "table": DisplayProfile(
                    label="Trials\nPer\nRun",
                    content_align="center",
                ),
            },
        )
    )

    # =====================================================
    # Derived Display Fields
    # =====================================================

    reg.register_display_field(
        DisplayField(
            field_name="display.current_ages",
            display_fn=current_ages_display,
            description=("Current ages of household members."),
            profiles={
                "table": DisplayProfile(
                    label="Age(s)",
                    content_align="center",
                )
            },
        )
    )

    # =====================================================
    # Run Execution Metrics
    # =====================================================

    reg.register_display_field(
        DisplayField(
            field_name="trial.completed",
            profiles={
                "table": DisplayProfile(
                    label="Done",
                    content_align="right",
                )
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="trial.pending",
            profiles={
                "table": DisplayProfile(
                    label="Pending",
                    content_align="right",
                )
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="trial.completion_rate",
            profiles={
                "table": DisplayProfile(
                    label="Complete\n%",
                    fmt="percent",
                    content_align="right",
                )
            },
        )
    )


# =========================================================
# Display Functions
# =========================================================


def current_ages_display(
    row,
):
    """
    Return household ages formatted as:

        62
        63/64
    """

    try:
        inputs = row["_inputs"]
        basic = inputs.get(
            "basic_info",
            {},
        )
        dob_list = basic.get(
            "date_of_birth",
            [],
        )
        if not dob_list:
            return None

        today = date.today()
        ages = []
        for dob_str in dob_list:
            dob = date.fromisoformat(dob_str)
            age = (
                today.year
                - dob.year
                - (
                    (
                        today.month,
                        today.day,
                    )
                    < (
                        dob.month,
                        dob.day,
                    )
                )
            )
            ages.append(str(age))

        return "/".join(ages)

    except Exception:
        return None
