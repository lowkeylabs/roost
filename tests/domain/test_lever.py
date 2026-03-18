# tests/domain/test_lever.py

from pathlib import Path

import pandas as pd

from owlroost.domain.models.case import Case
from owlroost.domain.services.lever import (
    compute_levers,
    compute_retirement_horizon,
    compute_spending_and_more,
)

# =========================================================
# Test Fixture Helpers
# =========================================================


def write_hfp(tmp_path: Path, names: list[str], wage_schedule: list[list[float]]) -> Path:
    file = tmp_path / "hfp.xlsx"

    writer = pd.ExcelWriter(file, engine="openpyxl")

    history_rows = 6

    for name, wages in zip(names, wage_schedule, strict=False):
        full_wages = [0] * history_rows + wages
        total_years = len(full_wages)

        years = list(range(2020, 2020 + total_years))

        df = pd.DataFrame(
            {
                "year": years,
                "anticipated wages": full_wages,
                "taxable ctrb": [0] * total_years,
                "401k ctrb": [0] * total_years,
                "Roth 401k ctrb": [0] * total_years,
                "IRA ctrb": [0] * total_years,
                "Roth IRA ctrb": [0] * total_years,
                "Roth conv": [0] * total_years,
                "big-ticket items": [0] * total_years,
            }
        )

        df.to_excel(writer, sheet_name=name, index=False)

    writer.close()
    return file


def write_case(tmp_path: Path, names: list[str], hfp_filename: str) -> Path:
    n = len(names)

    status = "married" if n == 2 else "single"

    name_entries = ", ".join(f'"{name}"' for name in names)
    dob_entries = ", ".join('"1960-01-01"' for _ in names)
    life_entries = ", ".join("85" for _ in names)

    taxable = ", ".join("100.0" for _ in names)
    tax_deferred = ", ".join("200.0" for _ in names)
    tax_free = ", ".join("50.0" for _ in names)

    pension_amounts = ", ".join("0" for _ in names)
    pension_ages = ", ".join("65.0" for _ in names)
    pension_indexed = ", ".join("false" for _ in names)

    ss_amounts = ", ".join("0" for _ in names)
    ss_ages = ", ".join("67.0" for _ in names)

    beneficiary_len = 1 if n == 1 else 3
    beneficiary = ", ".join("1.0" for _ in range(beneficiary_len))

    generic_block = ", ".join("[[60,40,0,0],[60,40,0,0]]" for _ in names)

    content = f"""
case_name = "{'+'.join(names)}"

[basic_info]
status = "{status}"
names = [{name_entries}]
date_of_birth = [{dob_entries}]
life_expectancy = [{life_entries}]
start_date = "2026-01-01"

[savings_assets]
taxable_savings_balances = [{taxable}]
tax_deferred_savings_balances = [{tax_deferred}]
tax_free_savings_balances = [{tax_free}]
beneficiary_fractions = [{beneficiary}]
spousal_surplus_deposit_fraction = 0.5

[household_financial_profile]
HFP_file_name = "{hfp_filename}"

[fixed_income]
pension_monthly_amounts = [{pension_amounts}]
pension_ages = [{pension_ages}]
pension_indexed = [{pension_indexed}]
social_security_pia_amounts = [{ss_amounts}]
social_security_ages = [{ss_ages}]

[rates_selection]
heirs_rate_on_tax_deferred_estate = 30.0
dividend_rate = 1.5
obbba_expiration_year = 2032
method = "user"
values = [5.0, 3.0, 2.0, 2.0]
from = 1928
to = 2025

[asset_allocation]
interpolation_method = "linear"
interpolation_center = 10.0
interpolation_width = 5.0
type = "individual"
generic = [{generic_block}]

[optimization_parameters]
spending_profile = "flat"
surviving_spouse_spending_percent = 60
objective = "maxSpending"
smile_dip = 15
smile_increase = 12
smile_delay = 0

[solver_options]
maxRothConversion = 400.0
noRothConversions = "None"
startRothConversions = 2026
bequest = 0
solver = "HiGHS"
spendingSlack = 0
amoRoth = true
amoSurplus = true
withSCLoop = true
withMedicare = "loop"
noLateSurplus = false
previousMAGIs = [200.0, 200.0]

[results]
default_plots = "today"
"""

    file = tmp_path / "case_test.toml"
    file.write_text(content.strip())
    return file


# =========================================================
# Retirement Horizon Tests
# =========================================================


def test_retirement_horizon_future_retirement(tmp_path):
    names = ["Alice"]
    wages = [[100000, 100000, 100000, 0, 0]]

    hfp = write_hfp(tmp_path, names, wages)
    case_file = write_case(tmp_path, names, hfp.name)

    case = Case(case_file)

    assert compute_retirement_horizon(case) == 3


def test_retirement_horizon_already_retired(tmp_path):
    names = ["Alice"]
    wages = [[0, 0, 0, 0]]

    hfp = write_hfp(tmp_path, names, wages)
    case_file = write_case(tmp_path, names, hfp.name)

    case = Case(case_file)

    assert compute_retirement_horizon(case) == 0


def test_retirement_horizon_never_retires(tmp_path):
    names = ["Alice"]
    wages = [[100000] * 20]

    hfp = write_hfp(tmp_path, names, wages)
    case_file = write_case(tmp_path, names, hfp.name)

    case = Case(case_file)

    assert compute_retirement_horizon(case) is None


# =========================================================
# Spending + Withdrawal Tests
# =========================================================


def test_spending_and_withdrawals_return_values(tmp_path):
    names = ["Alice"]
    wages = [[0, 0, 0, 0]]  # already retired

    hfp = write_hfp(tmp_path, names, wages)
    case_file = write_case(tmp_path, names, hfp.name)

    case = Case(case_file)

    spending, withdrawals = compute_spending_and_more(case)

    assert spending is not None
    assert spending > 0

    assert withdrawals is not None
    assert withdrawals >= 0


def test_withdrawals_less_than_or_equal_spending(tmp_path):
    names = ["Alice"]
    wages = [[50000, 50000, 0, 0]]

    hfp = write_hfp(tmp_path, names, wages)
    case_file = write_case(tmp_path, names, hfp.name)

    case = Case(case_file)

    spending, withdrawals = compute_spending_and_more(case)

    assert spending is not None
    assert withdrawals is not None

    # Because spending includes wages, withdrawals may be <= spending
    assert withdrawals <= spending


# =========================================================
# Combined Lever Summary Test
# =========================================================


def test_compute_levers_populates_all_fields(tmp_path):
    names = ["Alice"]
    wages = [[0, 0, 0, 0]]

    hfp = write_hfp(tmp_path, names, wages)
    case_file = write_case(tmp_path, names, hfp.name)

    case = Case(case_file)

    summary = compute_levers(case)

    assert summary.retirement_horizon == 0
    assert summary.max_spending is not None
    assert summary.first_year_total_withdrawals is not None
