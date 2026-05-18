# src/owlroost/display/overrides.py

from __future__ import annotations

from datetime import date

from owlplanner.socialsecurity import (
    getFRAs,
    getSelfFactor,
)

from owlroost.display.specs import (
    DisplayField,
    DisplayProfile,
)
from owlroost.display.utils import (
    normalize_input_money,
)

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
            field_name="session_id",
            path="_meta.session_id",
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
            description=("Compact hierarchical identifier " "case/session/run."),
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

    reg.register_display_field(
        DisplayField(
            field_name="optimization_parameters.objective",
            display_fn=make_abbreviation_display("optimization_parameters.objective"),
            profiles={
                "table": DisplayProfile(
                    label="Obj",
                    content_align="center",
                    label_align="center",
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="rates_selection.method",
            display_fn=make_abbreviation_display("rates_selection.method"),
            profiles={
                "table": DisplayProfile(
                    label="Rates",
                    content_align="left",
                    label_align="left",
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

    reg.register_display_field(
        DisplayField(
            field_name="display.life_expectancy",
            display_fn=life_expectancy_display,
            description="Household life expectancy values.",
            profiles={
                "table": DisplayProfile(
                    label="Life\nExp",
                    content_align="center",
                    label_align="center",
                ),
                "pivot": DisplayProfile(
                    label="Life Expectancy",
                    content_align="center",
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="display.taxable_savings",
            display_fn=taxable_savings_display,
            description=("Total taxable savings balances."),
            profiles={
                "table": DisplayProfile(
                    label="Taxable",
                    fmt="currency_short",
                    content_align="right",
                ),
                "pivot": DisplayProfile(
                    label="Taxable Savings",
                    fmt="currency_short",
                    content_align="right",
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="display.tax_deferred_savings",
            display_fn=tax_deferred_savings_display,
            description=("Total tax-deferred savings balances."),
            profiles={
                "table": DisplayProfile(
                    label="Tax\nDeferred",
                    fmt="currency_short",
                    content_align="right",
                    label_align="center",
                ),
                "pivot": DisplayProfile(
                    label="Tax Deferred Savings",
                    fmt="currency_short",
                    content_align="right",
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="display.tax_free_savings",
            display_fn=tax_free_savings_display,
            description=("Total tax-free savings balances."),
            profiles={
                "table": DisplayProfile(
                    label="Tax\nFree",
                    fmt="currency_short",
                    content_align="right",
                    label_align="center",
                ),
                "pivot": DisplayProfile(
                    label="Tax Free Savings",
                    fmt="currency_short",
                    content_align="right",
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="display.total_savings",
            display_fn=total_savings_display,
            description="Total savings balances across all account types.",
            profiles={
                "table": DisplayProfile(
                    label="Savings\nAssets",
                    fmt="currency_short",
                    content_align="right",
                ),
                "pivot": DisplayProfile(
                    label="Total Savings",
                    fmt="currency_short",
                    content_align="right",
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="display.fixed_income",
            display_fn=fixed_income_display,
            description=("Annual household guaranteed income " "in today's dollars."),
            profiles={
                "table": DisplayProfile(
                    label="Fixed\nIncome",
                    fmt="currency_short",
                    content_align="right",
                    label_align="center",
                ),
                "pivot": DisplayProfile(
                    label="Fixed Income",
                    fmt="currency_short",
                    content_align="right",
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="display.has_hfp_file",
            display_fn=has_hfp_file_display,
            description=("Whether a household financial profile " "spreadsheet is configured."),
            profiles={
                "table": DisplayProfile(
                    label="HFP?",
                    content_align="center",
                    label_align="center",
                ),
                "pivot": DisplayProfile(
                    label="HFP File",
                    content_align="center",
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="display.fixed_assets",
            display_fn=fixed_assets_display,
            description=("Total fixed assets loaded from HFP."),
            profiles={
                "table": DisplayProfile(
                    label="Fixed\nAssets",
                    fmt="currency_short",
                    content_align="right",
                    label_align="center",
                ),
                "pivot": DisplayProfile(
                    label="Fixed Assets",
                    fmt="currency_short",
                    content_align="right",
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="display.total_debts",
            display_fn=total_debts_display,
            description=("Total debts loaded from HFP."),
            profiles={
                "table": DisplayProfile(
                    label="Debt",
                    fmt="currency_short",
                    content_align="right",
                ),
                "pivot": DisplayProfile(
                    label="Total Debts",
                    fmt="currency_short",
                    content_align="right",
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="display.net_hfp_assets",
            display_fn=net_hfp_assets_display,
            description=("Fixed assets minus debts from HFP."),
            profiles={
                "table": DisplayProfile(
                    label="Net\nHFP",
                    fmt="currency_short",
                    content_align="right",
                    label_align="center",
                ),
                "pivot": DisplayProfile(
                    label="Net HFP Assets",
                    fmt="currency_short",
                    content_align="right",
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="display.has_fixed_assets",
            display_fn=has_fixed_assets_display,
            description=("Whether HFP fixed assets exist."),
            profiles={
                "table": DisplayProfile(
                    label="Fixed\nAst?",
                    content_align="center",
                    label_align="center",
                ),
                "pivot": DisplayProfile(
                    label="Has Fixed Assets",
                    content_align="center",
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="display.has_debts",
            display_fn=has_debts_display,
            description=("Whether HFP debts exist."),
            profiles={
                "table": DisplayProfile(
                    label="Debt?",
                    content_align="center",
                    label_align="center",
                ),
                "pivot": DisplayProfile(
                    label="Has Debts",
                    content_align="center",
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="display.total_balance_sheet",
            display_fn=total_balance_sheet_display,
            description=("Combined savings assets and HFP fixed assets."),
            profiles={
                "table": DisplayProfile(
                    label="Total\nAssets",
                    fmt="currency_short",
                    content_align="right",
                    label_align="center",
                ),
                "pivot": DisplayProfile(
                    label="Total Balance Sheet Assets",
                    fmt="currency_short",
                    content_align="right",
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="display.net_worth",
            display_fn=net_worth_display,
            description=("Savings plus fixed assets minus debts."),
            profiles={
                "table": DisplayProfile(
                    label="Net\nWorth",
                    fmt="currency_short",
                    content_align="right",
                    label_align="center",
                ),
                "pivot": DisplayProfile(
                    label="Net Worth",
                    fmt="currency",
                    content_align="right",
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="display.residence_value",
            display_fn=residence_value_display,
            description=("Residence value loaded from HFP."),
            profiles={
                "table": DisplayProfile(
                    label="Home",
                    fmt="currency_short",
                    content_align="right",
                ),
                "pivot": DisplayProfile(
                    label="Residence Value",
                    fmt="currency_short",
                    content_align="right",
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="display.mortgage_debt",
            display_fn=mortgage_debt_display,
            description=("Mortgage debt loaded from HFP."),
            profiles={
                "table": DisplayProfile(
                    label="Mortgage",
                    fmt="currency_short",
                    content_align="right",
                ),
                "pivot": DisplayProfile(
                    label="Mortgage Debt",
                    fmt="currency_short",
                    content_align="right",
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="display.social_security_income",
            display_fn=social_security_income_display,
            description=("Annual Social Security income " "in today's dollars."),
            profiles={
                "table": DisplayProfile(
                    label="Soc\nSec",
                    fmt="currency_short",
                    content_align="right",
                    label_align="center",
                ),
                "pivot": DisplayProfile(
                    label="Social Security Income",
                    fmt="currency_short",
                    content_align="right",
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="display.pension_income",
            display_fn=pension_income_display,
            description=("Annual pension income " "in today's dollars."),
            profiles={
                "table": DisplayProfile(
                    label="Pension",
                    fmt="currency_short",
                    content_align="right",
                ),
                "pivot": DisplayProfile(
                    label="Pension Income",
                    fmt="currency_short",
                    content_align="right",
                ),
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


def life_expectancy_display(
    row,
):
    """
    Return household life expectancy formatted as:

        72
        72/90
    """

    try:
        inputs = row.get(
            "_inputs",
            {},
        )

        basic = inputs.get(
            "basic_info",
            {},
        )

        values = basic.get(
            "life_expectancy",
            [],
        )

        if not values:
            return None

        return "/".join(str(int(v)) for v in values)

    except Exception:
        return None


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
        session_id = meta.get("session_id")
        run_id = meta.get("run_id")
        trial_id = meta.get("trial_id")

        # -------------------------------------------------
        # Missing core IDs
        # -------------------------------------------------

        if case_id is None or session_id is None or run_id is None:
            return None

        # -------------------------------------------------
        # Run-level
        # -------------------------------------------------

        if trial_id is None:
            return f"{case_id}/" f"{session_id}/" f"{run_id}"

        # -------------------------------------------------
        # Trial-level
        # -------------------------------------------------

        return f"{case_id}/" f"{session_id}/" f"{run_id}/" f"{trial_id}"

    except Exception:
        return None


def make_abbreviation_display(field_path):
    mapping = ABBREVIATIONS.get(field_path, {})

    path_parts = field_path.split(".")

    def display_fn(row):
        try:
            value = row.get("_inputs", {})

            for part in path_parts:
                value = value.get(part)

                if value is None:
                    return None

            return mapping.get(value, value)

        except Exception:
            return None

    return display_fn


def total_savings_display(
    row,
):
    try:
        inputs = row.get("_inputs", {})

        sa = inputs.get(
            "savings_assets",
            {},
        )

        total = 0.0

        for key in [
            "taxable_savings_balances",
            "tax_deferred_savings_balances",
            "tax_free_savings_balances",
        ]:
            values = sa.get(key, [])

            for v in values:
                total += normalize_input_money(
                    inputs,
                    v,
                )

        return total

    except Exception:
        return None


def fixed_income_display(
    row,
):
    """
    Annual guaranteed retirement income
    in today's dollars.

    Includes:
        - Social Security
        - pensions

    Uses OWL Social Security FRA and
    claiming-age adjustment rules.
    """

    try:
        inputs = row.get(
            "_inputs",
            {},
        )

        # =================================================
        # Sections
        # =================================================

        basic = inputs.get(
            "basic_info",
            {},
        )

        fixed = inputs.get(
            "fixed_income",
            {},
        )

        # =================================================
        # DOBs
        # =================================================

        dob_list = basic.get(
            "date_of_birth",
            [],
        )

        if not dob_list:
            return None

        yobs = []
        mobs = []
        tobs = []

        for dob_str in dob_list:
            dob = date.fromisoformat(dob_str)

            yobs.append(dob.year)
            mobs.append(dob.month)
            tobs.append(dob.day)

        # =================================================
        # Social Security
        # =================================================

        pias = fixed.get(
            "social_security_pia_amounts",
            [],
        )

        ss_ages = fixed.get(
            "social_security_ages",
            [],
        )

        fras = getFRAs(
            yobs,
            mobs,
            tobs,
        )

        annual_ss = 0.0

        for i in range(min(len(pias), len(ss_ages))):
            pia = float(pias[i] or 0.0)

            claim_age = float(ss_ages[i] or 0.0)

            born_on_first = tobs[i] == 1

            factor = getSelfFactor(
                fras[i],
                claim_age,
                born_on_first,
            )

            annual_ss += pia * 12.0 * factor

        # =================================================
        # Pension
        # =================================================

        pensions = fixed.get(
            "pension_monthly_amounts",
            [],
        )

        annual_pension = 0.0

        for p in pensions:
            annual_pension += float(p or 0) * 12.0

        # =================================================
        # Total
        # =================================================

        return annual_ss + annual_pension

    except Exception:
        return None


def has_hfp_file_display(
    row,
):
    """
    Return:

        Yes
        -

    based on whether an HFP file
    is configured.
    """

    try:
        inputs = row.get(
            "_inputs",
            {},
        )

        hfp = inputs.get(
            "household_financial_profile",
            {},
        )

        filename = hfp.get(
            "HFP_file_name",
        )

        if filename in (
            None,
            "",
            "None",
        ):
            return "-"

        return "Yes"

    except Exception:
        return "-"


def fixed_assets_display(
    row,
):
    """
    Total fixed assets from HFP.
    """

    try:
        hfp = row.get(
            "_hfp",
            {},
        )

        return hfp.get(
            "total_fixed_assets",
        )

    except Exception:
        return None


def total_debts_display(
    row,
):
    """
    Total debts from HFP.
    """

    try:
        hfp = row.get(
            "_hfp",
            {},
        )

        return hfp.get(
            "total_debts",
        )

    except Exception:
        return None


def net_hfp_assets_display(
    row,
):
    """
    Net HFP assets:

        fixed assets - debts
    """

    try:
        hfp = row.get(
            "_hfp",
            {},
        )

        assets = float(
            hfp.get(
                "total_fixed_assets",
                0.0,
            )
            or 0.0
        )

        debts = float(
            hfp.get(
                "total_debts",
                0.0,
            )
            or 0.0
        )

        return assets - debts

    except Exception:
        return None


def has_fixed_assets_display(
    row,
):
    """
    Return:

        Yes
        -

    based on whether HFP fixed assets exist.
    """

    try:
        hfp = row.get(
            "_hfp",
            {},
        )

        count = int(
            hfp.get(
                "fixed_asset_count",
                0,
            )
            or 0
        )

        return "Yes" if count > 0 else "-"

    except Exception:
        return "-"


def has_debts_display(
    row,
):
    """
    Return:

        Yes
        -

    based on whether HFP debts exist.
    """

    try:
        hfp = row.get(
            "_hfp",
            {},
        )

        count = int(
            hfp.get(
                "debt_count",
                0,
            )
            or 0
        )

        return "Yes" if count > 0 else "-"

    except Exception:
        return "-"


def total_balance_sheet_display(
    row,
):
    """
    Total household assets:

        savings assets + fixed assets
    """

    try:
        savings = float(total_savings_display(row) or 0.0)

        fixed_assets = float(fixed_assets_display(row) or 0.0)

        return savings + fixed_assets

    except Exception:
        return None


def net_worth_display(
    row,
):
    """
    Net worth estimate:

        savings
      + fixed assets
      - debts
    """

    try:
        savings = float(total_savings_display(row) or 0.0)

        fixed_assets = float(fixed_assets_display(row) or 0.0)

        debts = float(total_debts_display(row) or 0.0)

        return savings + fixed_assets - debts

    except Exception:
        return None


def residence_value_display(
    row,
):
    """
    Residence value from HFP.
    """

    try:
        hfp = row.get(
            "_hfp",
            {},
        )

        return hfp.get(
            "residence_value",
        )

    except Exception:
        return None


def mortgage_debt_display(
    row,
):
    """
    Mortgage debt from HFP.
    """

    try:
        hfp = row.get(
            "_hfp",
            {},
        )

        return hfp.get(
            "mortgage_debt",
        )

    except Exception:
        return None


def taxable_savings_display(
    row,
):
    """
    Total taxable savings balances.
    """

    try:
        inputs = row.get(
            "_inputs",
            {},
        )

        sa = inputs.get(
            "savings_assets",
            {},
        )

        total = 0.0

        values = sa.get(
            "taxable_savings_balances",
            [],
        )

        for v in values:
            total += normalize_input_money(
                inputs,
                v,
            )

        return total

    except Exception:
        return None


def tax_deferred_savings_display(
    row,
):
    """
    Total tax-deferred savings balances.
    """

    try:
        inputs = row.get(
            "_inputs",
            {},
        )

        sa = inputs.get(
            "savings_assets",
            {},
        )

        total = 0.0

        values = sa.get(
            "tax_deferred_savings_balances",
            [],
        )

        for v in values:
            total += normalize_input_money(
                inputs,
                v,
            )

        return total

    except Exception:
        return None


def tax_free_savings_display(
    row,
):
    """
    Total tax-free savings balances.
    """

    try:
        inputs = row.get(
            "_inputs",
            {},
        )

        sa = inputs.get(
            "savings_assets",
            {},
        )

        total = 0.0

        values = sa.get(
            "tax_free_savings_balances",
            [],
        )

        for v in values:
            total += normalize_input_money(
                inputs,
                v,
            )

        return total

    except Exception:
        return None


def social_security_income_display(
    row,
):
    """
    Annual Social Security income
    in today's dollars.

    Uses OWL FRA and claiming-age
    adjustment rules.
    """

    try:
        inputs = row.get(
            "_inputs",
            {},
        )

        # =================================================
        # Sections
        # =================================================

        basic = inputs.get(
            "basic_info",
            {},
        )

        fixed = inputs.get(
            "fixed_income",
            {},
        )

        # =================================================
        # DOBs
        # =================================================

        dob_list = basic.get(
            "date_of_birth",
            [],
        )

        if not dob_list:
            return None

        yobs = []
        mobs = []
        tobs = []

        for dob_str in dob_list:
            dob = date.fromisoformat(dob_str)

            yobs.append(dob.year)
            mobs.append(dob.month)
            tobs.append(dob.day)

        # =================================================
        # Social Security
        # =================================================

        pias = fixed.get(
            "social_security_pia_amounts",
            [],
        )

        ss_ages = fixed.get(
            "social_security_ages",
            [],
        )

        fras = getFRAs(
            yobs,
            mobs,
            tobs,
        )

        annual_ss = 0.0

        for i in range(
            min(
                len(pias),
                len(ss_ages),
            )
        ):
            pia = float(pias[i] or 0.0)

            claim_age = float(ss_ages[i] or 0.0)

            born_on_first = tobs[i] == 1

            factor = getSelfFactor(
                fras[i],
                claim_age,
                born_on_first,
            )

            annual_ss += pia * 12.0 * factor

        return annual_ss

    except Exception:
        return None


def pension_income_display(
    row,
):
    """
    Annual pension income
    in today's dollars.
    """

    try:
        inputs = row.get(
            "_inputs",
            {},
        )

        fixed = inputs.get(
            "fixed_income",
            {},
        )

        pensions = fixed.get(
            "pension_monthly_amounts",
            [],
        )

        annual_pension = 0.0

        for p in pensions:
            annual_pension += float(p or 0.0) * 12.0

        return annual_pension

    except Exception:
        return None
