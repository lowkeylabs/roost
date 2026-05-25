# src/owlroost/display/fields/provenance.py

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
    Register operational provenance and inventory fields.

    These fields focus on:
        - operational provenance
        - session discovery metadata
        - execution inventory
        - study/session organization

    This module intentionally focuses on
    operational organization and execution
    lineage rather than:
        - runtime execution state
        - computational scaling
        - financial outcomes
        - planning methodology
    """

    # =====================================================
    # Session Date
    # =====================================================

    reg.register_display_field(
        DisplayField(
            field_name="session.date",
            path="_meta.session.date",
            description=("Operational session date."),
            profiles={
                "table": DisplayProfile(
                    label="Date",
                    content_align="center",
                ),
                "pivot": DisplayProfile(
                    label="Session Date",
                    content_align="center",
                ),
            },
        )
    )

    # =====================================================
    # Session Time
    # =====================================================

    reg.register_display_field(
        DisplayField(
            field_name="session.time",
            path="_meta.session.time",
            description=("Operational session time."),
            profiles={
                "table": DisplayProfile(
                    label="Time",
                    content_align="center",
                ),
                "pivot": DisplayProfile(
                    label="Session Time",
                    content_align="center",
                ),
            },
        )
    )

    # =====================================================
    # Session Description
    # =====================================================

    reg.register_display_field(
        DisplayField(
            field_name="session.description",
            path="_meta.session.description",
            description=("Human-readable operational " "session description."),
            profiles={
                "table": DisplayProfile(
                    label="Description",
                    content_align="left",
                ),
                "pivot": DisplayProfile(
                    label="Session Description",
                    content_align="left",
                ),
            },
        )
    )

    # =====================================================
    # Session Count
    # =====================================================

    reg.register_display_field(
        DisplayField(
            field_name="session.count",
            description=("Number of discovered sessions."),
            profiles={
                "table": DisplayProfile(
                    label="Sessions",
                    content_align="right",
                ),
                "pivot": DisplayProfile(
                    label="Session Count",
                    content_align="right",
                ),
            },
        )
    )

    # =====================================================
    # Run Count
    # =====================================================

    reg.register_display_field(
        DisplayField(
            field_name="run.count",
            description=("Number of discovered runs."),
            profiles={
                "table": DisplayProfile(
                    label="Runs",
                    content_align="right",
                ),
                "pivot": DisplayProfile(
                    label="Run Count",
                    content_align="right",
                ),
            },
        )
    )

    # =====================================================
    # Trial Total
    # =====================================================

    reg.register_display_field(
        DisplayField(
            field_name="trial.total",
            description=("Total discovered trials."),
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
