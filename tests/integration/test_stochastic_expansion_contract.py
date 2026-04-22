# tests/integration/test_stochastic_expansion_contract.py

import tomllib
from pathlib import Path

from click.testing import CliRunner

from owlroost.cli.cmd_run import cmd_run

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------


def make_basic_case(tmp_path: Path) -> Path:
    case_file = tmp_path / "case.toml"
    case_file.write_text(
        """
case_name = "Alex+Jamie"
description = "A case where there is big difference in longevity."

[basic_info]
status = "married"
names = ["Alex", "Jamie"]
date_of_birth = ["1960-01-15", "1961-01-17"]
life_expectancy = [72, 90]
start_date = "2026-01-01"

[savings_assets]
taxable_savings_balances = [500.0, 200.0]
tax_deferred_savings_balances = [1500.0, 400.0]
tax_free_savings_balances = [50.0, 40.0]
beneficiary_fractions = [1.0, 1.0, 1.0]
spousal_surplus_deposit_fraction = 0.5

[fixed_income]
pension_monthly_amounts = [0, 0]
pension_ages = [65.0, 65.0]
pension_indexed = [false, false]
social_security_pia_amounts = [3000, 1200]
social_security_ages = [69.0, 62.083333333333336]

[rates_selection]
heirs_rate_on_tax_deferred_estate = 30.0
dividend_rate = 1.72
obbba_expiration_year = 2032
method = "user"
values = [7.0, 4.0, 3.3, 2.8]
from = 1928
to = 2025

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
previousMAGIs = [ 200.0, 200.0,]

[results]
default_plots = "today"
"""
    )

    # create dummy HFP file expected by OWL
    (tmp_path / "HFP_alex+jamie.xlsx").write_bytes(b"dummy")

    return case_file


def run_cli(runner: CliRunner, case_file: Path, *extra_args):
    return runner.invoke(
        cmd_run,
        [
            str(case_file),
            *extra_args,
        ],
    )


def load_trial(tmp_path: Path, trial_id: int) -> dict:
    results_root = tmp_path / "results"
    trial_dir = next(results_root.rglob(f"trials/{trial_id:04d}"))
    eff_path = next(trial_dir.glob("*_effective.toml"))
    return tomllib.loads(eff_path.read_text())


def get_effective_path(tmp_path: Path, trial_id: int) -> Path:
    results_root = tmp_path / "results"
    trial_dir = next(results_root.rglob(f"trials/{trial_id:04d}"))
    return next(trial_dir.glob("*_effective.toml"))


# ------------------------------------------------------------
# TESTS
# ------------------------------------------------------------


def test_single_trial_no_seed_injection(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    case_file = make_basic_case(tmp_path)

    runner = CliRunner()
    result = run_cli(runner, case_file)

    assert result.exit_code == 0

    trial0 = load_trial(tmp_path, 0)

    # Should use deterministic case values
    assert trial0["basic_info"]["life_expectancy"] == [72, 90]
    assert "longevity" not in trial0 or "calculated_life_expectancy" not in trial0.get(
        "longevity", {}
    )


def test_multi_trial_injects_seeds(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    case_file = make_basic_case(tmp_path)

    runner = CliRunner()

    result = run_cli(
        runner,
        case_file,
        "longevity=default",
        "longevity.apply_to_plan=false",
        "--trials=3",
    )

    assert result.exit_code == 0

    trial0 = load_trial(tmp_path, 0)
    trial1 = load_trial(tmp_path, 1)

    assert "master_seed" in trial0["roost"]
    assert trial0["roost"]["rates_seed"] != trial1["roost"]["rates_seed"]
    assert trial0["roost"]["longevity_seed"] != trial1["roost"]["longevity_seed"]


def test_longevity_not_applied_when_flag_false(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    case_file = make_basic_case(tmp_path)

    runner = CliRunner()
    result = run_cli(
        runner,
        case_file,
        "longevity=default",
        "longevity.apply_to_plan=false",
        "--trials=2",
    )

    assert result.exit_code == 0

    trial0 = load_trial(tmp_path, 0)

    # base values unchanged
    assert trial0["basic_info"]["life_expectancy"] == [72, 90]
    assert "calculated_life_expectancy" in trial0["longevity"]


def test_longevity_overwrites_when_enabled(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    case_file = make_basic_case(tmp_path)

    runner = CliRunner()
    result = run_cli(
        runner,
        case_file,
        "longevity=default",
        "longevity.apply_to_plan=true",
        "--trials=2",
    )

    assert result.exit_code == 0

    trial0 = load_trial(tmp_path, 0)

    base = trial0["longevity"]["base_life_expectancy"]
    calc = trial0["longevity"]["calculated_life_expectancy"]

    assert trial0["basic_info"]["life_expectancy"] == calc
    assert base != calc


def test_longevity_override_auto_activates_group(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    case_file = make_basic_case(tmp_path)

    runner = CliRunner()
    result = run_cli(
        runner,
        case_file,
        "longevity.apply_to_plan=true",
        "--trials=2",
    )

    assert result.exit_code == 0

    trial0 = load_trial(tmp_path, 0)

    assert "longevity" in trial0
    assert trial0["longevity"]["model"] == "default"


def test_promoted_effective_runs_as_is(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    case_file = make_basic_case(tmp_path)

    runner = CliRunner()

    result = run_cli(runner, case_file, "--trials=2")
    print("FIRST RUN EXIT:", result.exit_code)
    print("FIRST RUN OUTPUT:")
    print(result.output)
    assert result.exit_code == 0

    load_trial(tmp_path, 0)
    eff_path = get_effective_path(tmp_path, 0)

    print("\n===== EFFECTIVE TOML =====")
    print(eff_path.read_text())

    promoted = tmp_path / "promoted.toml"
    promoted.write_text(eff_path.read_text())

    print("\n===== PROMOTED TOML =====")
    print(promoted.read_text())

    result2 = run_cli(runner, promoted)
    print("SECOND RUN EXIT:", result2.exit_code)
    print("SECOND RUN OUTPUT:")
    print(result2.output)

    assert result2.exit_code == 0
