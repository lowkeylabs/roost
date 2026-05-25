# src/owlroost/display/fields/balances.py

from __future__ import annotations

from datetime import date

from owlplanner.socialsecurity import (
    getFRAs,
    getSelfFactor,
)

from owlroost.display.specs import (
    DisplayField,
    DisplayProfile,
    ExplainSpec,
)
from owlroost.display.utils import (
    normalize_input_money,
)

# =========================================================
# Registration
# =========================================================


def register_display_fields(
    reg,
):
    """
    Register household balance-sheet display fields.

    These fields intentionally operate directly from:

        - _inputs
        - _hfp

    rather than requiring runtime-generated metrics.

    This allows:
        - case-level views
        - run-level views
        - compare views
        - study overlays

    to share a common semantic display layer.
    """

    # =====================================================
    # Household Ages
    # =====================================================

    reg.register_display_field(
        DisplayField(
            field_name="display.current_ages",
            display_fn=current_ages_display,
            description="Current household ages.",
            explain=ExplainSpec(sources=["derived"], units="years"),
            profiles={
                "table": DisplayProfile(
                    label="Ages",
                    content_align="center",
                ),
                "pivot": DisplayProfile(
                    label="Current Ages",
                    content_align="center",
                ),
            },
        )
    )

    # =====================================================
    # Life Expectancy
    # =====================================================

    reg.register_display_field(
        DisplayField(
            field_name="display.life_expectancy",
            display_fn=life_expectancy_display,
            description="Expected household longevity.",
            explain=ExplainSpec(sources=["derived"], units="years"),
            profiles={
                "table": DisplayProfile(
                    label="Life\nExp",
                    content_align="center",
                ),
                "pivot": DisplayProfile(
                    label="Life Expectancy",
                    content_align="center",
                ),
            },
        )
    )

    # =====================================================
    # Net Worth
    # =====================================================

    reg.register_display_field(
        DisplayField(
            field_name="display.net_worth",
            display_fn=net_worth_display,
            description="Approximate household net worth.",
            explain=ExplainSpec(sources=["derived"], units="dollars - annual"),
            profiles={
                "table": DisplayProfile(
                    label="Net\nWorth",
                    fmt="currency_short",
                    content_align="right",
                ),
                "pivot": DisplayProfile(
                    label="Net Worth",
                    fmt="currency_short",
                    content_align="right",
                ),
            },
        )
    )

    # =====================================================
    # Total Balance Sheet
    # =====================================================

    reg.register_display_field(
        DisplayField(
            field_name="display.total_balance_sheet",
            display_fn=total_balance_sheet_display,
            description=("Combined savings assets and HFP fixed assets."),
            explain=ExplainSpec(sources=["derived"], units="dollars - annual"),
            profiles={
                "table": DisplayProfile(
                    label="Total\nAssets",
                    fmt="currency_short",
                    content_align="right",
                    label_align="center",
                ),
                "pivot": DisplayProfile(
                    label="Total Assets",
                    fmt="currency_short",
                    content_align="right",
                ),
            },
        )
    )

    # =====================================================
    # Savings
    # =====================================================

    reg.register_display_field(
        DisplayField(
            field_name="display.total_savings",
            display_fn=total_savings_display,
            description="Total retirement savings.",
            explain=ExplainSpec(sources=["derived"], units="dollars - annual"),
            profiles={
                "table": DisplayProfile(
                    label="Savings",
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
            field_name="display.taxable_savings",
            display_fn=taxable_savings_display,
            description="Taxable retirement savings.",
            explain=ExplainSpec(sources=["derived"], units="dollars - annual"),
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
            description="Tax-deferred retirement savings.",
            explain=ExplainSpec(sources=["derived"], units="dollars - annual"),
            profiles={
                "table": DisplayProfile(
                    label="Tax Def",
                    fmt="currency_short",
                    content_align="right",
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
            description="Tax-free retirement savings.",
            explain=ExplainSpec(sources=["derived"], units="dollars - annual"),
            profiles={
                "table": DisplayProfile(
                    label="Tax Free",
                    fmt="currency_short",
                    content_align="right",
                ),
                "pivot": DisplayProfile(
                    label="Tax Free Savings",
                    fmt="currency_short",
                    content_align="right",
                ),
            },
        )
    )

    # =====================================================
    # HFP Presence
    # =====================================================

    reg.register_display_field(
        DisplayField(
            field_name="display.has_hfp_file",
            display_fn=has_hfp_file_display,
            description="Whether an HFP spreadsheet is configured.",
            explain=ExplainSpec(
                sources=["derived"],
            ),
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
            field_name="display.has_fixed_assets",
            display_fn=has_fixed_assets_display,
            description="Whether HFP fixed assets exist.",
            explain=ExplainSpec(
                sources=["derived"],
            ),
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
            description="Whether HFP debts exist.",
            explain=ExplainSpec(
                sources=["derived"],
            ),
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

    # =====================================================
    # HFP Financials
    # =====================================================

    reg.register_display_field(
        DisplayField(
            field_name="display.net_hfp_assets",
            display_fn=net_hfp_assets_display,
            description="Net household financial profile assets.",
            explain=ExplainSpec(
                sources=["derived"],
            ),
            profiles={
                "table": DisplayProfile(
                    label="Net HFP",
                    fmt="currency_short",
                    content_align="right",
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
            field_name="display.fixed_assets",
            display_fn=fixed_assets_display,
            description="Fixed non-retirement assets.",
            explain=ExplainSpec(sources=["derived"], units="dollars - annual"),
            profiles={
                "table": DisplayProfile(
                    label="Fixed\nAssets",
                    fmt="currency_short",
                    content_align="right",
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
            description="Total household liabilities.",
            explain=ExplainSpec(sources=["derived"], units="dollars - annual"),
            profiles={
                "table": DisplayProfile(
                    label="Total\nLiable",
                    fmt="currency_short",
                    content_align="right",
                ),
                "pivot": DisplayProfile(
                    label="Total Liabilities",
                    fmt="currency_short",
                    content_align="right",
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="display.residence_value",
            display_fn=residence_value_display,
            description="Residence value loaded from HFP.",
            explain=ExplainSpec(sources=["derived"], units="dollars - annual"),
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
            explain=ExplainSpec(sources=["derived"], units="dollars - annual"),
            description="Mortgage debt loaded from HFP.",
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

    # =====================================================
    # Guaranteed Income
    # =====================================================

    reg.register_display_field(
        DisplayField(
            field_name="display.social_security_income",
            display_fn=social_security_income_display,
            description="Estimated annual Social Security income.",
            explain=ExplainSpec(sources=["derived"], units="dollars - annual"),
            profiles={
                "table": DisplayProfile(
                    label="SS\nIncome",
                    fmt="currency_short",
                    content_align="right",
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
            description="Estimated annual pension income.",
            explain=ExplainSpec(sources=["derived"], units="dollars - annual"),
            profiles={
                "table": DisplayProfile(
                    label="Pension\nIncome",
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

    reg.register_display_field(
        DisplayField(
            field_name="display.fixed_income",
            display_fn=fixed_income_display,
            description="Combined guaranteed retirement income.",
            explain=ExplainSpec(sources=["derived"], units="dollars - monthly"),
            profiles={
                "table": DisplayProfile(
                    label="Fixed\nIncome",
                    fmt="currency_short",
                    content_align="right",
                ),
                "pivot": DisplayProfile(
                    label="Fixed Income",
                    fmt="currency_short",
                    content_align="right",
                ),
            },
        )
    )


# =========================================================
# Helpers
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


# =========================================================
# Display Functions
# =========================================================


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


def life_expectancy_display(
    row,
):
    try:
        basic = get_inputs(row).get("basic_info", {})

        values = basic.get(
            "life_expectancy",
            [],
        )

        return "/".join(str(x) for x in values)

    except Exception:
        return None


def total_savings_display(
    row,
):
    try:
        inputs = get_inputs(row)

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
            for v in sa.get(key, []):
                total += normalize_input_money(
                    inputs,
                    v,
                )

        return total

    except Exception:
        return None


def taxable_savings_display(
    row,
):
    try:
        inputs = get_inputs(row)

        sa = inputs.get(
            "savings_assets",
            {},
        )

        return safe_sum(
            normalize_input_money(inputs, v)
            for v in sa.get(
                "taxable_savings_balances",
                [],
            )
        )

    except Exception:
        return None


def tax_deferred_savings_display(
    row,
):
    try:
        inputs = get_inputs(row)

        sa = inputs.get(
            "savings_assets",
            {},
        )

        return safe_sum(
            normalize_input_money(inputs, v)
            for v in sa.get(
                "tax_deferred_savings_balances",
                [],
            )
        )

    except Exception:
        return None


def tax_free_savings_display(
    row,
):
    try:
        inputs = get_inputs(row)

        sa = inputs.get(
            "savings_assets",
            {},
        )

        return safe_sum(
            normalize_input_money(inputs, v)
            for v in sa.get(
                "tax_free_savings_balances",
                [],
            )
        )

    except Exception:
        return None


def has_hfp_file_display(
    row,
):
    try:
        hfp = get_inputs(row).get("household_financial_profile", {})

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


def has_fixed_assets_display(
    row,
):
    try:
        count = int(
            get_hfp(row).get(
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
    try:
        count = int(
            get_hfp(row).get(
                "debt_count",
                0,
            )
            or 0
        )

        return "Yes" if count > 0 else "-"

    except Exception:
        return "-"


def fixed_assets_display(
    row,
):
    try:
        return get_hfp(row).get(
            "total_fixed_assets",
        )

    except Exception:
        return None


def total_debts_display(
    row,
):
    try:
        return get_hfp(row).get(
            "total_debts",
        )

    except Exception:
        return None


def net_hfp_assets_display(
    row,
):
    try:
        assets = fixed_assets_display(row) or 0

        debts = total_debts_display(row) or 0

        return assets - debts

    except Exception:
        return None


def residence_value_display(
    row,
):
    try:
        return get_hfp(row).get(
            "residence_value",
        )

    except Exception:
        return None


def mortgage_debt_display(
    row,
):
    try:
        return get_hfp(row).get(
            "mortgage_debt",
        )

    except Exception:
        return None


def social_security_income_display(
    row,
):
    try:
        inputs = get_inputs(row)

        basic = inputs.get(
            "basic_info",
            {},
        )

        fixed = inputs.get(
            "fixed_income",
            {},
        )

        dob_list = basic.get(
            "date_of_birth",
            [],
        )

        yobs = []
        mobs = []
        tobs = []

        for dob_str in dob_list:
            dob = date.fromisoformat(dob_str)

            yobs.append(dob.year)
            mobs.append(dob.month)
            tobs.append(dob.day)

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

        return float(annual_ss)

    except Exception:
        return None


def pension_income_display(
    row,
):
    try:
        fixed = get_inputs(row).get("fixed_income", {})

        pensions = fixed.get(
            "pension_monthly_amounts",
            [],
        )

        return safe_sum(float(p or 0.0) * 12.0 for p in pensions)

    except Exception:
        return None


def fixed_income_display(
    row,
):
    try:
        return (social_security_income_display(row) or 0) + (pension_income_display(row) or 0)

    except Exception:
        return None


def total_balance_sheet_display(
    row,
):
    try:
        savings = total_savings_display(row) or 0

        fixed_assets = fixed_assets_display(row) or 0

        return savings + fixed_assets

    except Exception:
        return None


def net_worth_display(
    row,
):
    try:
        savings = total_savings_display(row) or 0

        hfp = net_hfp_assets_display(row) or 0

        return savings + hfp

    except Exception:
        return None
