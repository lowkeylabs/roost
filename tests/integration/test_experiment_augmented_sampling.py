# tests/integration/test_experiment_augmented_sampling.py

import tomllib
from pathlib import Path

from click.testing import CliRunner

from owlroost.cli.cmd_run import cmd_run

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------


def make_case(tmp_path: Path) -> Path:
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


def load_effective_files(tmp_path: Path):
    results_root = tmp_path / "results"
    return list(results_root.rglob("*_effective.toml"))


# ------------------------------------------------------------
# TEST
# ------------------------------------------------------------


def test_historical_complete_multiple_slices(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    case_file = make_case(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        cmd_run,
        [
            str(case_file),
            "experiment=augmented_sampling",
            "rates_selection.from_to=[[1966,1970],[1988,1992]]",
            "--trial-jobs=1",
            "--run-jobs=1",
        ],
    )

    assert result.exit_code == 0

    effective_files = load_effective_files(tmp_path)

    # 1966–1970 → S=5 → 10 runs
    # 1988–1992 → S=5 → 10 runs
    # total expected = 20
    assert len(effective_files) == 20

    seen = set()

    for eff in effective_files:
        data = tomllib.loads(eff.read_text())
        rates = data["rates_selection"]

        start, end = rates["from_to"]

        key = (
            start,
            end,
            rates["roll_sequence"],
            rates["reverse_sequence"],
        )

        seen.add(key)

    # Ensure full unique coverage
    expected = set()

    for start, end in [(1966, 1970), (1988, 1992)]:
        S = end - start + 1
        for roll in range(S):
            for reverse in [False, True]:
                expected.add((start, end, roll, reverse))

    assert seen == expected
