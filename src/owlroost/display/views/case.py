# src/owlroost/display/views/case.py

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
            level="case",
            name="build",
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
