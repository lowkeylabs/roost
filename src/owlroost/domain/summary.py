from .registry import Column, register_column

# ---------------------------------------------------------
# Basic Info Group
# ---------------------------------------------------------

register_column(
    Column(
        key="case_name",
        label="Case",
        extractor=lambda c: c.name,
        group="basic",
    )
)

register_column(
    Column(
        key="household",
        label="Household",
        extractor=lambda c: ", ".join(c.household_names),
        group="basic",
    )
)

register_column(
    Column(
        key="total_assets",
        label="Total Assets",
        extractor=lambda c: c.total_assets,
        group="assets",
    )
)

register_column(
    Column(
        key="objective",
        label="Objective",
        extractor=lambda c: c.objective,
        group="optimization",
    )
)
