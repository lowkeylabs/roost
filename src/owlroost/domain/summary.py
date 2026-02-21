from .registry import (
    VIEW_REGISTRY,
    Column,
    register_column,
    register_view,
)

# ---------------------------------------------------------
# BASIC
# ---------------------------------------------------------

register_column(
    Column(
        key="case_name",
        label="Case",
        extractor=lambda c: c.name,
        group="basic",
        align="left",
        fmt="truncate_20",
    )
)

register_column(
    Column(
        key="start_year",
        label="Start\nyear",
        extractor=lambda c: c.start_year,
        group="basic",
        align="center",
        fmt="int",
    )
)


register_column(
    Column(
        key="household",
        label="Household",
        extractor=lambda c: c.household_names,
        group="basic",
        align="left",
    )
)

register_column(
    Column(
        key="ages",
        label="Ages",
        extractor=lambda c: c.ages,
        group="basic",
        align="left",
    )
)

register_column(
    Column(
        key="life_expectancy",
        label="Life Exp",
        extractor=lambda c: c.life_expectancies,
        group="basic",
        align="left",
    )
)

register_column(
    Column(
        key="total_assets",
        label="Savings\n($k)",
        extractor=lambda c: c.total_assets,
        group="basic",
        align="right",
        fmt="float1",
    )
)

register_column(
    Column(
        key="pensions",
        label="Pension\n($k/mo)",
        extractor=lambda c: c.pension_monthly,
        fmt="float1_dash",
        group="basic",
        align="left",
    )
)

register_column(
    Column(
        key="pension_ages",
        label="Pension\nAge",
        extractor=lambda c: c.pension_ages,
        group="basic",
        align="left",
        fmt="int",
    )
)

register_column(
    Column(
        key="ss_pia",
        label="SS PIA\n($/mo)",
        extractor=lambda c: c.social_security_pia,
        group="basic",
        align="left",
        fmt="float0_dash",
    )
)

register_column(
    Column(
        key="ss_ages",
        label="SS Age",
        extractor=lambda c: c.social_security_ages,
        group="basic",
        align="left",
        fmt="int",
    )
)

# ---------------------------------------------------------
# ASSETS
# ---------------------------------------------------------

register_column(
    Column(
        key="taxable",
        label="Taxable",
        extractor=lambda c: c.taxable_assets,
        group="assets",
        align="right",
        fmt="currency",
    )
)

register_column(
    Column(
        key="tax_deferred",
        label="Tax-Deferred",
        extractor=lambda c: c.tax_deferred_assets,
        group="assets",
        align="right",
        fmt="currency",
    )
)

register_column(
    Column(
        key="tax_free",
        label="Tax-Free",
        extractor=lambda c: c.tax_free_assets,
        group="assets",
        align="right",
        fmt="currency",
    )
)


# ---------------------------------------------------------
# OPTIMIZATION
# ---------------------------------------------------------

register_column(
    Column(
        key="objective",
        label="Objective",
        extractor=lambda c: c.objective,
        group="optimization",
        align="left",
    )
)

register_column(
    Column(
        key="spending_profile",
        label="Spending",
        extractor=lambda c: c.spending_profile,
        group="optimization",
        align="left",
    )
)

register_column(
    Column(
        key="solver",
        label="Solver",
        extractor=lambda c: c.config.solver_options.get("solver"),
        group="optimization",
        align="left",
    )
)

# ---------------------------------------------------------
# REGISTER VIEWS
# ---------------------------------------------------------

register_view(
    "basic",
    [
        "case_name",
        "start_year",
        "household",
        "ages",
        "life_expectancy",
        "total_assets",
        "pensions",
        "pension_ages",
        "ss_pia",
        "ss_ages",
    ],
)

register_view(
    "assets",
    ["case_name", "total_assets", "taxable", "tax_deferred", "tax_free"],
)

register_view(
    "optimization",
    ["case_name", "objective", "spending_profile", "solver"],
)

# ---------------------------------------------------------
# ALL VIEW (after other views exist)
# ---------------------------------------------------------

all_columns = []
for cols in VIEW_REGISTRY.values():
    for key in cols:
        if key not in all_columns:
            all_columns.append(key)

register_view("all", all_columns)
