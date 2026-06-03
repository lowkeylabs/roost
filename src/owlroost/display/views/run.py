# src/owlroost/display/views/run.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from owlroost.display.specs import (
    DisplayView,
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

    reg.register_view(
        DisplayView(
            level="run",
            name="run",
            entries=[
                # =====================================
                # Identity
                # =====================================
                "case_name",
                ("description", {"modes": ["pivot"]}),
            ],
            description=(""),
        )
    )

    reg.register_view(
        DisplayView(
            level="run",
            name="results",
            entries=[
                # =====================================
                # Identity
                # =====================================
                "case_name",
                ("description", {"modes": ["pivot"]}),
            ],
            description=(""),
        )
    )
