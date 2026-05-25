# src/owlroost/display/fields/identity.py

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
    Register identity and hierarchy display fields.

    These fields define operational identifiers used
    throughout ROOST display systems.

    Identity fields are intentionally operational and
    projection-oriented.

    They are reused across:
        - case views
        - session views
        - run views
        - trial views
        - study overlays
        - provenance reports
    """

    # =====================================================
    # Hierarchical IDs
    # =====================================================

    reg.register_display_field(
        DisplayField(
            field_name="case_id",
            path="_meta.case_id",
            description="Operational case identifier.",
            profiles={
                "table": DisplayProfile(
                    label="Case",
                    content_align="right",
                ),
                "pivot": DisplayProfile(
                    label="Case",
                    content_align="right",
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="session_id",
            path="_meta.session_id",
            description="Operational session identifier.",
            profiles={
                "table": DisplayProfile(
                    label="Sess",
                    content_align="right",
                ),
                "pivot": DisplayProfile(
                    label="Session",
                    content_align="right",
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="run_id",
            path="_meta.run_id",
            description="Operational run identifier.",
            profiles={
                "table": DisplayProfile(
                    label="Run",
                    content_align="right",
                ),
                "pivot": DisplayProfile(
                    label="Run",
                    content_align="right",
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="trial_id",
            path="_meta.trial_id",
            description="Operational trial identifier.",
            profiles={
                "table": DisplayProfile(
                    label="Trial",
                    content_align="right",
                ),
                "pivot": DisplayProfile(
                    label="Trial",
                    content_align="right",
                ),
            },
        )
    )

    # =====================================================
    # Compact Hierarchical Identifier
    # =====================================================

    reg.register_display_field(
        DisplayField(
            field_name="compact_id",
            display_fn=compact_id_display,
            description=("Compact hierarchical operational " "identifier."),
            profiles={
                "table": DisplayProfile(
                    label="ID",
                    content_align="center",
                ),
                "pivot": DisplayProfile(
                    label="ID",
                    content_align="center",
                ),
            },
        )
    )


# =========================================================
# Display Functions
# =========================================================


def compact_id_display(
    row,
):
    """
    Return compact hierarchical identifier.

    Examples:

        Case:
            0

        Session:
            0/1

        Run:
            0/1/0

        Trial:
            0/1/0/12
    """

    try:
        meta = row.get(
            "_meta",
            {},
        )

        case_id = meta.get(
            "case_id",
        )

        session_id = meta.get(
            "session_id",
        )

        run_id = meta.get(
            "run_id",
        )

        trial_id = meta.get(
            "trial_id",
        )

        # =================================================
        # Missing Core IDs
        # =================================================

        if case_id is None:
            return None

        # =================================================
        # Case Level
        # =================================================

        if session_id is None:
            return f"{case_id}"

        # =================================================
        # Session Level
        # =================================================

        if run_id is None:
            return f"{case_id}/" f"{session_id}"

        # =================================================
        # Run Level
        # =================================================

        if trial_id is None:
            return f"{case_id}/" f"{session_id}/" f"{run_id}"

        # =================================================
        # Trial Level
        # =================================================

        return f"{case_id}/" f"{session_id}/" f"{run_id}/" f"{trial_id}"

    except Exception:
        return None
