# tests/integration/test_historical_rate_path.py

import shutil
from pathlib import Path

import numpy as np
import pandas as pd
from click.testing import CliRunner

from owlroost.cli.cmd_run import cmd_run

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------


def make_historical_case(tmp_path: Path) -> Path:
    case_file = tmp_path / "case.toml"
    case_file.write_text(
        """
case_name = "Taylor+Morgan"
description = "Minimal historical test case."

[basic_info]
status = "married"
names = ["Taylor", "Morgan"]
date_of_birth = ["1960-01-01", "1961-01-01"]
life_expectancy = [85, 85]
start_date = "2026-01-01"

[savings_assets]
taxable_savings_balances = [1000.0, 500.0]
tax_deferred_savings_balances = [0.0, 0.0]
tax_free_savings_balances = [0.0, 0.0]
beneficiary_fractions = [1.0, 1.0, 1.0]
spousal_surplus_deposit_fraction = 0.5

[fixed_income]
pension_monthly_amounts = [0, 0]
pension_ages = [65.0, 65.0]
pension_indexed = [false, false]
social_security_pia_amounts = [2000, 2000]
social_security_ages = [67.0, 67.0]

[household_financial_profile]
HFP_file_name = ""

[rates_selection]
heirs_rate_on_tax_deferred_estate = 30.0
dividend_rate = 1.72
obbba_expiration_year = 2032
method = "historical"
from = 1980
to = 1983
roll_sequence = 0
reverse_sequence = false

[asset_allocation]
interpolation_method = "linear"
interpolation_center = 15.0
interpolation_width = 5.0
type = "individual"
generic = [
  [[60, 40, 0, 0], [60, 40, 0, 0]],
  [[60, 40, 0, 0], [60, 40, 0, 0]]
]

[optimization_parameters]
spending_profile = "flat"
surviving_spouse_spending_percent = 60
objective = "maxSpending"

[solver_options]
bequest = 0
solver = "HiGHS"

[results]
default_plots = "today"
"""
    )
    return case_file


def clear_results(tmp_path: Path):
    results_dir = tmp_path / "results"
    if results_dir.exists():
        shutil.rmtree(results_dir)


def find_rates_file(tmp_path: Path) -> Path:
    results_root = tmp_path / "results"
    return next(results_root.rglob("*_rates.xlsx"))


def load_rates_df(tmp_path: Path) -> pd.DataFrame:
    rates_path = find_rates_file(tmp_path)
    return pd.read_excel(rates_path, sheet_name="Rates")


# ------------------------------------------------------------
# TESTS
# ------------------------------------------------------------


def test_rates_file_is_created_and_loadable(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    case_file = make_historical_case(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        cmd_run,
        [str(case_file)],
    )

    print(result.output)
    print(result.stderr)
    print(result.stdout)
    assert result.exit_code == 0

    df = load_rates_df(tmp_path)

    assert not df.empty

    expected_columns = [
        "Year",
        "S&P 500",
        "Corporate Baa",
        "T Bonds",
        "inflation",
    ]

    for col in expected_columns:
        assert col in df.columns


def test_roll_sequence_changes_rate_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    # ---- baseline
    case_file = make_historical_case(tmp_path)
    result = runner.invoke(
        cmd_run,
        [str(case_file)],
    )
    assert result.exit_code == 0
    baseline = load_rates_df(tmp_path)

    clear_results(tmp_path)

    # ---- roll=1
    case_file_roll = make_historical_case(tmp_path)
    text = case_file_roll.read_text().replace("roll_sequence = 0", "roll_sequence = 1")
    case_file_roll.write_text(text)

    result2 = runner.invoke(
        cmd_run,
        [str(case_file)],
    )
    assert result2.exit_code == 0
    rolled = load_rates_df(tmp_path)

    base_vec = baseline["S&P 500"].to_numpy()
    rolled_vec = rolled["S&P 500"].to_numpy()

    expected = np.roll(base_vec, 1)

    assert np.allclose(rolled_vec, expected)


def test_reverse_sequence_changes_rate_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    # ---- baseline
    case_file = make_historical_case(tmp_path)
    result = runner.invoke(
        cmd_run,
        [str(case_file)],
    )
    assert result.exit_code == 0
    baseline = load_rates_df(tmp_path)

    clear_results(tmp_path)

    # ---- reverse=true
    case_file_rev = make_historical_case(tmp_path)
    text = case_file_rev.read_text().replace("reverse_sequence = false", "reverse_sequence = true")
    case_file_rev.write_text(text)

    result2 = runner.invoke(
        cmd_run,
        [str(case_file)],
    )
    assert result2.exit_code == 0
    reversed_df = load_rates_df(tmp_path)

    # First year of reversed should equal last year of baseline
    assert reversed_df.iloc[0]["S&P 500"] == baseline.iloc[-1]["S&P 500"]
