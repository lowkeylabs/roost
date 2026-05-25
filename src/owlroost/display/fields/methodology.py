# src/owlroost/display/fields/methodology.py

from __future__ import annotations

from owlroost.display.formatting import format_value
from owlroost.display.specs import (
    DisplayField,
    DisplayProfile,
)
from owlroost.display.utils import (
    get_units_multiplier,
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
# Registration
# =========================================================


def register_display_fields(
    reg,
):
    """
    Register methodology and planning display fields.

    These fields define:
        - retirement planning methodology
        - optimization strategy
        - rates methodology
        - computational planning configuration

    This module intentionally focuses on:
        - analytical methodology
        - planning semantics
        - experiment configuration

    NOT:
        - runtime execution
        - scaling
        - provenance
        - financial balances
    """

    # =====================================================
    # Optimization Objective
    # =====================================================

    reg.register_display_field(
        DisplayField(
            field_name="optimization_parameters.objective",
            display_fn=make_abbreviation_display("optimization_parameters.objective"),
            description=("Retirement optimization objective."),
            profiles={
                "table": DisplayProfile(
                    label="Obj",
                    content_align="center",
                    label_align="center",
                ),
                "pivot": DisplayProfile(
                    label="Objective",
                    content_align="center",
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="solver_options.bequest",
            description="Minimum bequest constraint.",
            profiles={
                "table": DisplayProfile(
                    label="Beq",
                    fmt="currency0",
                    content_align="right",
                ),
                "pivot": DisplayProfile(
                    label="Bequest Constraint",
                    fmt="currency0",
                    content_align="right",
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="solver_options.netSpending",
            description="Net spending target.",
            profiles={
                "table": DisplayProfile(
                    label="NetSpd",
                    fmt="currency0",
                    content_align="right",
                ),
                "pivot": DisplayProfile(
                    label="Net Spending Target",
                    fmt="currency0",
                    content_align="right",
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="display.optimization_goal",
            display_fn=compute_optimization_goal,
            description=("Combined optimization objective " "and associated target."),
            profiles={
                "table": DisplayProfile(
                    label="Goal",
                    content_align="center",
                    label_align="center",
                ),
                "pivot": DisplayProfile(
                    label="Optimization Goal",
                    content_align="center",
                ),
            },
        )
    )

    # =====================================================
    # Rates Methodology
    # =====================================================

    reg.register_display_field(
        DisplayField(
            field_name="rates_selection.method",
            display_fn=make_abbreviation_display("rates_selection.method"),
            description=("Rates sampling methodology."),
            profiles={
                "table": DisplayProfile(
                    label="Rates",
                    content_align="left",
                    label_align="left",
                ),
                "pivot": DisplayProfile(
                    label="Rates Method",
                    content_align="left",
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="display.rates_window",
            display_fn=compute_rates_window,
            description=("Historical rates selection window."),
            profiles={
                "table": DisplayProfile(
                    label="Rates\nWindow",
                    content_align="center",
                    label_align="center",
                ),
                "pivot": DisplayProfile(
                    label="Rates Window",
                    content_align="center",
                ),
            },
        )
    )

    # =====================================================
    # Trials Per Run
    # =====================================================

    reg.register_display_field(
        DisplayField(
            field_name="roost_runtime.trials_per_run",
            description=("Configured stochastic trials " "executed per run."),
            profiles={
                "table": DisplayProfile(
                    label="Trials\nPer\nRun",
                    content_align="center",
                    label_align="center",
                ),
                "pivot": DisplayProfile(
                    label="Trials Per Run",
                    content_align="center",
                ),
            },
        )
    )

    # =====================================================
    # Workers Per Run
    # =====================================================

    reg.register_display_field(
        DisplayField(
            field_name="roost_runtime.workers_per_run",
            description=("Configured worker concurrency " "per run."),
            profiles={
                "table": DisplayProfile(
                    label="Workers\nPer Run",
                    content_align="center",
                    label_align="center",
                ),
                "pivot": DisplayProfile(
                    label="Workers Per Run",
                    content_align="center",
                ),
            },
        )
    )


# =========================================================
# Display Functions
# =========================================================


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
