# src/owlroost/display/fields/design.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
Methodology display fields.

Notes
-----
Synthetic display fields used by
planning and methodology views.

These fields provide catalog identity
and presentation metadata for
computed methodology displays and
profile overrides for methodology-
related variables.
"""

from __future__ import annotations

from datetime import date

from owlroost.core.utils import normalize_module_path
from owlroost.display.formatting import format_value
from owlroost.display.operations.normalize import (
    get_units_multiplier,
)
from owlroost.display.specs import (
    DisplayField,
    DisplayProfile,
)

# =========================================================
# Abbreviations
# =========================================================

ABBREVIATIONS = {
    "optimization_parameters.objective": {
        "maxSpending": "mxSpd",
        "maxBequest": "mxBeq",
    },
    "rates_selection.method": {
        "historical average": "histAvg",
        "historical": "hist",
        "bootstrap_sor": "bSOR",
        "histolognormal": "hLogNorm",
    },
}

# =========================================================
# Methodology Ontology
# =========================================================

METHODOLOGY_ONTOLOGY = dict(
    owner="ROOST",
    semantic_domain="design",
    value_origin="roost-computed",
    projection_kind="synthetic",
    analytic_kind="observed",
    materialization_level="display",
    node_type="variable",
    defined_in=normalize_module_path(__file__),
)

DISPLAY_ONTOLOGY = dict(
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
    Register methodology display fields.
    """

    # =====================================================
    # Optimization Goal
    # =====================================================

    reg.register_display_field(
        DisplayField.field(
            "display.optimization_goal",
            display_fn=compute_optimization_goal,
            description=("Combined optimization objective and associated target."),
            profiles={
                "table": DisplayProfile(
                    label="Goal",
                    width=12,
                ),
                "pivot": DisplayProfile(
                    label="Optimization Goal",
                    width=24,
                ),
            },
            **METHODOLOGY_ONTOLOGY,
        )
    )

    # =====================================================
    # Rates Window
    # =====================================================

    reg.register_display_field(
        DisplayField.field(
            "display.rates_window",
            display_fn=compute_rates_window,
            description=("Historical rates selection window."),
            profiles={
                "table": DisplayProfile(
                    label="Rates\nWindow",
                    width=12,
                ),
                "pivot": DisplayProfile(
                    label="Rates Window",
                    width=18,
                ),
            },
            **METHODOLOGY_ONTOLOGY,
        )
    )

    # =====================================================
    # Trials Per Run
    # =====================================================

    reg.register_display_field(
        DisplayField.field(
            "roost_settings.trials_per_run",
            profiles={
                "table": DisplayProfile(
                    label="Trials\nPer\nRun",
                    width=10,
                ),
                "pivot": DisplayProfile(
                    label="Trials Per Run",
                    width=16,
                ),
            },
        )
    )

    # =====================================================
    # Rates Method
    # =====================================================

    reg.register_display_field(
        DisplayField.field(
            "rates_selection.method",
            description=("Rates sampling methodology."),
            profiles={
                "table": DisplayProfile(
                    label="Rates",
                    width=10,
                ),
                "pivot": DisplayProfile(
                    label="Rates Method",
                    width=16,
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField.field(
            field_name="display.completion_fraction",
            display_fn=completion_ratio_display,
            description=("Completed trials relative to configured trials per run."),
            profiles={
                "table": DisplayProfile(
                    label="Trials",
                    content_align="center",
                ),
                "pivot": DisplayProfile(
                    label="Completion Fraction",
                    content_align="center",
                ),
            },
            **DISPLAY_ONTOLOGY,
        )
    )

    reg.register_display_field(
        DisplayField.field(
            field_name="display.starting_ages",
            display_fn=current_ages_display,
            description=("Ages of household members (Start Date - DOB)"),
            profiles={
                "table": DisplayProfile(
                    label="Start\nAge(s)",
                    content_align="center",
                ),
                "pivot": DisplayProfile(
                    label="Ages(s) on OWL start date",
                    content_align="center",
                ),
            },
            **DISPLAY_ONTOLOGY,
        )
    )

    reg.register_display_field(
        DisplayField.field(
            field_name="basic_info.life_expectancy",
            profiles={
                "table": DisplayProfile(
                    label="Expect\nAge(s)",
                    content_align="center",
                ),
                "pivot": DisplayProfile(
                    label="Life expectancy(ies)",
                    content_align="center",
                ),
            },
        )
    )


# =========================================================
# Display Functions
# =========================================================


def get_inputs(
    row,
):
    return row.get(
        "_inputs",
        {},
    )


def get_hfp(
    row,
):
    return row.get(
        "_hfp",
        {},
    )


def safe_sum(
    values,
):
    return sum(float(v or 0) for v in values)


def make_abbreviation_display(
    field_path,
):
    """
    Build abbreviation display function.

    Maps long-form semantic values to compact
    operational display abbreviations.

    Examples:

        maxSpending -> mxSpd
        historical  -> hist
    """

    mapping = ABBREVIATIONS.get(
        field_path,
        {},
    )

    path_parts = field_path.split(".")

    def display_fn(
        row,
    ):
        try:
            value = row.get(
                "_inputs",
                {},
            )

            for part in path_parts:
                value = value.get(
                    part,
                )

                if value is None:
                    return None

            return mapping.get(
                value,
                value,
            )

        except Exception:
            return None

    return display_fn


def compute_optimization_goal(row):
    """
    Combined optimization goal display.

    Examples:

        mxSpd/$0
        mxBeq/$180K
        mxBeq/$1.2M
    """

    # -----------------------------------------------------
    # Objective abbreviation
    # -----------------------------------------------------

    objective_short = make_abbreviation_display("optimization_parameters.objective")(row)

    if objective_short is None:
        return None

    # -----------------------------------------------------
    # Inputs
    # -----------------------------------------------------

    inputs = row.get(
        "_inputs",
        {},
    )

    solver = inputs.get(
        "solver_options",
        {},
    )

    objective = inputs.get(
        "optimization_parameters",
        {},
    ).get(
        "objective",
    )

    # -----------------------------------------------------
    # Select relevant value
    # -----------------------------------------------------

    if objective == "maxSpending":
        value = solver.get("bequest")

    elif objective == "maxBequest":
        value = solver.get("netSpending")

    else:
        return objective_short

    # -----------------------------------------------------
    # No associated value
    # -----------------------------------------------------

    if value is None:
        return objective_short

    # -----------------------------------------------------
    # Convert OWL-scaled units -> dollars
    # -----------------------------------------------------

    units = solver.get(
        "units",
        "k",
    )

    multiplier = get_units_multiplier(
        units,
    )

    canonical_dollars = float(value) * multiplier

    # -----------------------------------------------------
    # Compact currency formatting
    # -----------------------------------------------------

    formatted = format_value(
        canonical_dollars,
        fmt="currency_short",
    )

    return f"{objective_short}/{formatted}"


def compute_rates_window(row):
    """
    Combined historical rates window.

    Examples:

        1928-2025
        1960-1975
    """

    inputs = row.get(
        "_inputs",
        {},
    )

    rates = inputs.get(
        "rates_selection",
        {},
    )

    start = rates.get("from")
    end = rates.get("to")

    if start is None or end is None:
        return None

    return f"{start}-{end}"


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
                "roost_settings",
                {},
            )
            .get("trials_per_run")
        )

        if completed is None or total is None:
            return "."

        return f"{completed}/{total}"

    except Exception:
        return "."


def current_ages_display(
    row,
):
    try:
        basic = get_inputs(row).get("basic_info", {})

        dob_values = basic.get(
            "date_of_birth",
            [],
        )

        start_date_str = basic.get(
            "start_date",
        )

        if not dob_values or not start_date_str:
            return None

        start = date.fromisoformat(start_date_str)

        ages = []

        for dob_str in dob_values:
            dob = date.fromisoformat(dob_str)

            age = start.year - dob.year - ((start.month, start.day) < (dob.month, dob.day))

            ages.append(age)

        return "/".join(str(x) for x in ages)

    except Exception:
        return None
