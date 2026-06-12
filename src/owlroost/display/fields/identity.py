# src/owlroost/display/fields/identity.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
Identity display fields.

Notes
-----
Operational identifiers used throughout
ROOST execution and provenance systems.
"""

from __future__ import annotations

from owlroost.catalog.ontology import (
    CatalogNodeType,
)
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
    analytic_kind="primary",
    materialization_level="run",
    node_type=CatalogNodeType.VARIABLE,
    defined_in=normalize_module_path(__file__),
)

COMPACT_ID_ONTOLOGY = dict(
    owner="ROOST",
    semantic_domain="execution",
    value_origin="roost-computed",
    projection_kind="synthetic",
    analytic_kind="primary",
    materialization_level="row",
    node_type=CatalogNodeType.VARIABLE,
    defined_in=normalize_module_path(__file__),
)

SUPERSESSION_ONTOLOGY = dict(
    owner="ROOST",
    semantic_domain="execution",
    value_origin="roost-computed",
    projection_kind="canonical",
    analytic_kind="primary",
    materialization_level="row",
    node_type=CatalogNodeType.VARIABLE,
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
            "display.compact_id",
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
            **COMPACT_ID_ONTOLOGY,
        )
    )

    # =====================================================
    # Supersession
    # =====================================================

    reg.register_display_field(
        DisplayField.field(
            "display.is_superseded",
            path="_meta.is_superseded",
            description=("True if this row has been superseded by a newer equivalent row."),
            profiles={
                "table": DisplayProfile(
                    label="Superseded",
                    width=10,
                    content_align="center",
                ),
                "pivot": DisplayProfile(
                    label="Superseded",
                    width=10,
                    content_align="center",
                ),
            },
            **SUPERSESSION_ONTOLOGY,
        )
    )

    reg.register_display_field(
        DisplayField.field(
            "display.compact_threads",
            description="Compact display of math libraries environment flag settings.",
            display_fn=compact_threads_display,
            derived_from=[
                "roost_environment.MKL_NUM_THREADS",
                "roost_environment.MSK_IPAR_NUM_THREADS",
                "roost_environment.OMP_NUM_THREADS",
                "roost_environment.OPENBLAS_NUM_THREADS",
            ],
            profiles={
                "table": DisplayProfile(
                    label="MSK/MKL/\nOMP/BLAS",
                    content_align="center",
                ),
                "pivot": DisplayProfile(
                    label="MSK MKL OMP BLAS",
                    content_align="center",
                ),
            },
            **COMPACT_ID_ONTOLOGY,
        )
    )

    reg.register_display_field(
        DisplayField.field(
            "display.superseded_by",
            path="_meta.superseded_by",
            description=("Compact identifier of the row that superseded this row."),
            profiles={
                "table": DisplayProfile(
                    label="Superseded By",
                    width=12,
                    content_align="center",
                ),
                "pivot": DisplayProfile(
                    label="Superseded By",
                    width=12,
                    content_align="center",
                ),
            },
            **SUPERSESSION_ONTOLOGY,
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


def compact_threads_display(
    row,
):
    """
    Return compact runtime thread summary.

    Format:

        MSK/MKL/OMP/BLAS

    Example:

        2/4/4/4
    """

    try:
        runtime_env = row.get(
            "_inputs",
            {},
        ).get(
            "roost_environment",
            {},
        )

        msk = runtime_env.get(
            "MSK_IPAR_NUM_THREADS",
            "-",
        )

        mkl = runtime_env.get(
            "MKL_NUM_THREADS",
            "-",
        )

        omp = runtime_env.get(
            "OMP_NUM_THREADS",
            "-",
        )

        blas = runtime_env.get(
            "OPENBLAS_NUM_THREADS",
            "-",
        )

        return f"{msk}/{mkl}/{omp}/{blas}"

    except Exception:
        return None
