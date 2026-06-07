# src/owlroost/display/fields/identity.py
#
# Copyright (c) 2026 John Leonard
# All rights reserved.
# SPDX-License-Identifier: LicenseRef-OwlRoost-Proprietary
# See LICENSE file in repository root.

"""
Identity display fields.

Notes
-----
Operational identifiers used throughout
ROOST execution and provenance systems.
"""

from __future__ import annotations

from owlroost.core.utils import normalize_module_path
from owlroost.display.specs import (
    DisplayField,
    DisplayProfile,
)

# =========================================================
# Ontology
# =========================================================

IDENTITY_ONTOLOGY = dict(
    owner="ROOST",
    semantic_domain="execution",
    value_origin="roost-computed",
    projection_kind="canonical",
    analytic_kind="observed",
    materialization_level="run",
    node_type="variable",
    defined_in=normalize_module_path(__file__),
)

# =========================================================
# Registration
# =========================================================


def register_display_fields(
    reg,
):
    """
    Register operational identity fields.
    """

    # =====================================================
    # Canonical IDs
    # =====================================================

    reg.register_display_field(
        DisplayField.field(
            "case_id",
            path="_meta.case_id",
            description="Operational case identifier.",
            profiles={
                "table": DisplayProfile(
                    label="Case",
                    content_align="right",
                ),
            },
            **IDENTITY_ONTOLOGY,
        )
    )

    reg.register_display_field(
        DisplayField.field(
            "session_id",
            path="_meta.session_id",
            description="Operational session identifier.",
            profiles={
                "table": DisplayProfile(
                    label="Sess",
                    content_align="right",
                ),
            },
            **IDENTITY_ONTOLOGY,
        )
    )

    reg.register_display_field(
        DisplayField.field(
            "run_id",
            path="_meta.run_id",
            description="Operational run identifier.",
            profiles={
                "table": DisplayProfile(
                    label="Run",
                    content_align="right",
                ),
            },
            **IDENTITY_ONTOLOGY,
        )
    )

    reg.register_display_field(
        DisplayField.field(
            "trial_id",
            path="_meta.trial_id",
            description="Operational trial identifier.",
            profiles={
                "table": DisplayProfile(
                    label="Trial",
                    content_align="right",
                ),
            },
            **IDENTITY_ONTOLOGY,
        )
    )

    # =====================================================
    # Compact ID
    # =====================================================

    reg.register_display_field(
        DisplayField.field(
            "compact_id",
            description="Compact hierarchical operational identifier.",
            display_fn=compact_id_display,
            derived_from=[
                "case_id",
                "session_id",
                "run_id",
                "trial_id",
            ],
            profiles={
                "table": DisplayProfile(
                    label="ID",
                    width=12,
                    content_align="center",
                ),
                "pivot": DisplayProfile(
                    label="ID",
                    width=12,
                    content_align="center",
                ),
            },
            **IDENTITY_ONTOLOGY,
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

        0
        0/0
        0/0/0
        0/0/0/0
    """

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

    if case_id is None:
        return None

    if session_id is None:
        return f"{case_id}"

    if run_id is None:
        return f"{case_id}/{session_id}"

    if trial_id is None:
        return f"{case_id}/{session_id}/{run_id}"

    return f"{case_id}/{session_id}/{run_id}/{trial_id}"
