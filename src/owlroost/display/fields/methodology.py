# src/owlroost/display/fields/methodology.py

from __future__ import annotations

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
