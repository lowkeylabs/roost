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
        label="Plan\nstart",
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
        key="total_savings",
        label="Savings\n($k)",
        extractor=lambda c: c.total_savings,
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
        key="taxable_savings",
        label="Taxable\n($k)",
        extractor=lambda c: c.taxable_savings,
        group="assets",
        align="right",
        fmt="currency",
    )
)

register_column(
    Column(
        key="tax_deferred_savings",
        label="Tax-def\n($k)",
        extractor=lambda c: c.tax_deferred_savings,
        group="assets",
        align="right",
        fmt="currency",
    )
)

register_column(
    Column(
        key="tax_free_savings",
        label="Tax-Free\n($k)",
        extractor=lambda c: c.tax_free_savings,
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


register_column(
    Column(
        key="initial_asset_allocation",
        label="Initial allocations (%)\n[S&P,Bonds,T-Notes,Cash]",
        extractor=lambda c: c.initial_asset_allocation,
        group="assets",
        align="left",
        fmt="allocation",
    )
)

# ---------------------------------------------------------
# LONGEVITY
# ---------------------------------------------------------

register_column(
    Column(
        key="life_expectancy",
        label="OWL\nLife Exp",
        extractor=lambda c: c.life_expectancies,
        group="longevity",
        align="left",
        fmt="int",
    )
)

register_column(
    Column(
        key="longevity_percentiles",
        label="Longevity\nPct-tiles",
        extractor=lambda c: c.longevity_percentiles,
        group="longevity",
        align="left",
        fmt="float2",
    )
)

register_column(
    Column(
        key="longevity_health",
        label="Health",
        extractor=lambda c: c.longevity_health,
        group="longevity",
        align="left",
    )
)

register_column(
    Column(
        key="longevity_sex",
        label="Sex",
        extractor=lambda c: c.longevity_sex,
        group="longevity",
        align="left",
    )
)

register_column(
    Column(
        key="longevity_smoker",
        label="Smoker",
        extractor=lambda c: c.longevity_smoker,
        group="longevity",
        align="left",
    )
)

register_column(
    Column(
        key="extensions",
        label="Ext",
        extractor=lambda c: (
            ("L" if c.has_longevity_section else "") + ("R" if c.has_roost_section else "")
        ),
        group="basic",
        align="center",
    )
)

# ---------------------------------------------------------
# EXTENSION FLAGS
# ---------------------------------------------------------

register_column(
    Column(
        key="has_longevity_section",
        label="Lon",
        extractor=lambda c: "✓" if c.has_longevity_section else "",
        group="basic",
        align="center",
    )
)

register_column(
    Column(
        key="has_roost_section",
        label="Roost",
        extractor=lambda c: "✓" if c.has_roost_section else "",
        group="basic",
        align="center",
    )
)

register_column(
    Column(
        key="deterministic_life_ages",
        label="GM Model\nLife Exp",
        extractor=lambda c: c.deterministic_life_ages,
        group="longevity",
        align="left",
        fmt="int",
    )
)

# ---------------------------------------------------------
# REGISTER VIEWS
# ---------------------------------------------------------

register_view(
    "basic",
    [
        "household",
        "start_year",
        "ages",
        "total_savings",
        "pensions",
        "pension_ages",
        "ss_pia",
        "ss_ages",
        "extensions",
    ],
)

register_view(
    "assets",
    [
        "household",
        "start_year",
        "total_savings",
        "taxable_savings",
        "tax_deferred_savings",
        "tax_free_savings",
        "initial_asset_allocation",
    ],
)

register_view(
    "longevity",
    [
        "household",
        "ages",
        "life_expectancy",
        "deterministic_life_ages",
        "longevity_percentiles",
        "longevity_health",
        "longevity_sex",
        "longevity_smoker",
    ],
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
