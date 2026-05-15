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
    # Hierarchical IDs
    # =====================================================

    reg.register_display_field(
        DisplayField(
            field_name="case_id",
            path="_meta.case_id",
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
            field_name="experiment_id",
            path="_meta.experiment_id",
            profiles={
                "table": DisplayProfile(
                    label="Exp",
                    content_align="right",
                ),
                "pivot": DisplayProfile(
                    label="Experiment",
                    content_align="right",
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="run_id",
            path="_meta.run_id",
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

    reg.register_display_field(
        DisplayField(
            field_name="compact_id",
            display_fn=compact_id_display,
            description=("Compact hierarchical identifier " "case/experiment/run."),
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

    # =====================================================
    # Planning
    # =====================================================

    reg.register_display_field(
        DisplayField(
            field_name="roost_runtime.trials_per_run",
            profiles={
                "table": DisplayProfile(
                    label="Trials\nPer\nRun",
                    content_align="center",
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="roost_runtime.workers_per_run",
            profiles={
                "table": DisplayProfile(
                    label="Workers\nPer Run",
                    content_align="center",
                    label_align="center",
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

    reg.register_display_field(
        DisplayField(
            field_name="run_timing.elapsed_seconds",
            profiles={
                "table": DisplayProfile(
                    label="Run\nSeconds",
                    fmt="float3",
                    content_align="right",
                ),
                "pivot": DisplayProfile(
                    label="Run Seconds",
                    fmt="float3",
                    content_align="right",
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="timing.elapsed_seconds__median",
            profiles={
                "table": DisplayProfile(
                    label="Trial\nMedian\nSec",
                    fmt="float3",
                    content_align="right",
                ),
                "pivot": DisplayProfile(
                    label="Trial Median Sec",
                    fmt=".2f",
                    content_align="right",
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="timing.elapsed_seconds__mean",
            profiles={
                "table": DisplayProfile(
                    label="Trial\nMean\nSec",
                    fmt="float3",
                    content_align="right",
                ),
                "pivot": DisplayProfile(
                    label="Trial Mean Sec",
                    fmt="float3",
                    content_align="right",
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="completion_ratio",
            display_fn=completion_ratio_display,
            description=("Completed trials relative " "to configured trials per run."),
            profiles={
                "table": DisplayProfile(
                    label="Trials",
                    content_align="center",
                ),
                "pivot": DisplayProfile(
                    label="Completion Ratio",
                    content_align="center",
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="roost_runtime.math_library_threads",
            description=("math library threads used to set ENV strings."),
            profiles={
                "table": DisplayProfile(
                    label="Math\nThreads", content_align="center", label_align="center"
                ),
                "pivot": DisplayProfile(
                    label="Math library threads", content_align="center", label_align="center"
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="runtime_environment.MSK_IPAR_NUM_THREADS",
            description=("MOSEK-specific environment setting."),
            profiles={
                "table": DisplayProfile(
                    label="MSK IPAR\nTHREADS", content_align="center", label_align="center"
                ),
                "pivot": DisplayProfile(
                    label="MSK IPAR NUM THREADS", content_align="center", label_align="center"
                ),
            },
        )
    )


# =========================================================
# Display Functions
# =========================================================


def completion_ratio_display(row):
    completed = row.get("_metrics", {}).get("trial.completed")

    total = row.get("_inputs", {}).get("roost_runtime", {}).get("trials_per_run")

    if completed is None or total is None:
        return "."

    return f"{completed}/{total}"


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


def compact_id_display(
    row,
):
    """
    Return compact hierarchical identifier.

    Examples:
        0/0/0
        0/1/0
        2/4/7

    Trial rows:
        0/1/0/12
    """

    try:
        meta = row.get(
            "_meta",
            {},
        )

        case_id = meta.get("case_id")
        experiment_id = meta.get("experiment_id")
        run_id = meta.get("run_id")
        trial_id = meta.get("trial_id")

        # -------------------------------------------------
        # Missing core IDs
        # -------------------------------------------------

        if case_id is None or experiment_id is None or run_id is None:
            return None

        # -------------------------------------------------
        # Run-level
        # -------------------------------------------------

        if trial_id is None:
            return f"{case_id}/" f"{experiment_id}/" f"{run_id}"

        # -------------------------------------------------
        # Trial-level
        # -------------------------------------------------

        return f"{case_id}/" f"{experiment_id}/" f"{run_id}/" f"{trial_id}"

    except Exception:
        return None
