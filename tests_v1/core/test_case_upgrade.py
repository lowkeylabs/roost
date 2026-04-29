from io import StringIO

from owlplanner.config.plan_bridge import config_to_plan

from owlroost.core.case_upgrade import case_upgrade
from owlroost.domain.models.case import Case


def test_case_upgrade_preserves_rates_selection_from_when_modifying(tmp_path):
    """
    Ensure that when case_upgrade modifies the case
    (e.g. injects longevity section), the [rates_selection]
    'from' field is preserved and not rewritten as 'from_'.
    """

    content = """
case_name = "Alice"

[basic_info]
status = "single"
names = ["Alice"]
date_of_birth = ["1960-01-01"]
life_expectancy = [85]
start_date = "2025-01-01"

[savings_assets]
taxable_savings_balances = [100.0]
tax_deferred_savings_balances = [200.0]
tax_free_savings_balances = [50.0]
beneficiary_fractions = [1.0]
spousal_surplus_deposit_fraction = 0.5

[household_financial_profile]
HFP_file_name = "dummy.xlsx"

[fixed_income]
pension_monthly_amounts = [0]
pension_ages = [65.0]
pension_indexed = [false]
social_security_pia_amounts = [0]
social_security_ages = [67.0]

[rates_selection]
heirs_rate_on_tax_deferred_estate = 30.0
dividend_rate = 1.5
obbba_expiration_year = 2032
method = "historical"
from = 1969
to = 2001

[asset_allocation]
interpolation_method = "linear"
interpolation_center = 10.0
interpolation_width = 5.0
type = "individual"
generic = [[[60,40,0,0]]]

[optimization_parameters]
spending_profile = "smile"
surviving_spouse_spending_percent = 60
objective = "maxSpending"
smile_dip = 15
smile_increase = 12
smile_delay = 0


[solver_options]
solver = "HiGHS"

[results]
default_plots = "today"
"""

    case_file = tmp_path / "case_test.toml"
    case_file.write_text(content.strip())

    case = Case(case_file)

    # Force upgrade to modify case (inject longevity + roost)
    case_upgrade(case, write=True)

    written = case_file.read_text()

    assert "from =" in written
    assert "from_ =" not in written


def test_full_rebuild_write_preserves_rates_from(tmp_path):
    """
    This test mimics the real CLI behavior:

    1. Load a real-style TOML with method="historical average"
    2. Build Case (which rebuilds internal model)
    3. Call write()
    4. Ensure 'from' is not rewritten as 'from_'
    """

    content = """
case_name = "joe"

[basic_info]
status = "single"
names = ["Joe"]
date_of_birth = ["1967-01-15"]
life_expectancy = [89]
start_date = "2026-01-01"

[savings_assets]
taxable_savings_balances = [338.5]
tax_deferred_savings_balances = [650.2]
tax_free_savings_balances = [60.6]

[household_financial_profile]
HFP_file_name = "HFP_joe.xlsx"

[fixed_income]
pension_monthly_amounts = [0]
pension_ages = [65.0]
pension_indexed = [true]
social_security_pia_amounts = [2360]
social_security_ages = [67.0]

[rates_selection]
heirs_rate_on_tax_deferred_estate = 30.0
dividend_rate = 1.8
obbba_expiration_year = 2032
method = "historical average"
from = 1969
to = 2002

[asset_allocation]
interpolation_method = "s-curve"
interpolation_center = 15.0
interpolation_width = 5.0
type = "individual"
generic = [[[60,40,0,0]]]

[optimization_parameters]
spending_profile = "smile"
objective = "maxSpending"

[solver_options]
solver = "default"

[results]
default_plots = "nominal"
"""

    case_file = tmp_path / "case_joe.toml"
    case_file.write_text(content.strip())

    # Load into Case (this triggers config_dict_to_model)
    case = Case(case_file)

    # Simulate real workflow: write back out
    case.write()

    written = case_file.read_text()

    # 🔴 This SHOULD fail right now
    assert "from =" in written
    assert "from_ =" not in written


def test_plan_build_then_write_preserves_from(tmp_path):
    """
    Reproduce the real workflow:
    - Load case
    - Build plan via config_to_plan
    - Solve plan
    - Write case
    Ensure 'from' is preserved.
    """

    content = """
case_name = "joe"
description = "This is an example of a case involving a single individual. Joe is single and will retire in a few years. His wages and contributions are contained in the 'HFP_joe.xlsx' Household Financial Profile."

[basic_info]
status = "single"
names = [ "Joe",]
date_of_birth = [ "1967-01-15",]
life_expectancy = [ 89,]
start_date = "2026-01-01"

[savings_assets]
taxable_savings_balances = [ 338.5,]
tax_deferred_savings_balances = [ 650.2,]
tax_free_savings_balances = [ 60.6,]

[household_financial_profile]
HFP_file_name = "HFP_joe.xlsx"

[fixed_income]
pension_monthly_amounts = [ 0.0,]
pension_ages = [ 65.0,]
pension_indexed = [ true,]
social_security_pia_amounts = [ 2360,]
social_security_ages = [ 67.0,]
social_security_trim_pct = 0

[rates_selection]
heirs_rate_on_tax_deferred_estate = 30.0
dividend_rate = 1.8
obbba_expiration_year = 2032
method = "historical average"
from = 1969
to = 2002
reproducible_rates = false
reverse_sequence = false
roll_sequence = 0

[asset_allocation]
interpolation_method = "s-curve"
interpolation_center = 15.0
interpolation_width = 5.0
type = "individual"
generic = [ [ [ 60, 40, 0, 0,], [ 70, 30, 0, 0,],],]

[optimization_parameters]
spending_profile = "smile"
surviving_spouse_spending_percent = 60
objective = "maxSpending"
smile_dip = 15
smile_increase = 12
smile_delay = 0

[solver_options]
maxRothConversion = 50
startRothConversions = 2026
bequest = 300
withSCLoop = true
withMedicare = "loop"
solver = "default"

[results]
default_plots = "nominal"
"""

    case_file = tmp_path / "case_joe.toml"
    case_file.write_text(content.strip())

    case = Case(case_file)

    # 🔥 Build plan (this may mutate internal config structure)
    raw = case._raw_dict
    plan = config_to_plan(
        raw,
        dirname=str(case_file.parent),
        loadHFP=False,
        verbose=False,
        logstreams=[StringIO(), StringIO()],
    )

    plan.solve(plan.objective, plan.solverOptions)

    # Now write back out
    case.write()

    written = case_file.read_text()

    # 🔴 This is the real corruption check
    assert "from =" in written
    assert "from_ =" not in written
