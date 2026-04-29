import json
from io import StringIO

from owlplanner.config.plan_bridge import config_to_plan

from owlroost.core.metrics_from_plan import write_metrics_json
from owlroost.domain.models.case import Case

CONTENT = """
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
generic = [[[60,40,0,0], [60,40,0,0]]]

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


def _build_and_solve_plan(case_file):
    case = Case(case_file)

    raw = case._raw_dict

    plan = config_to_plan(
        raw,
        dirname=str(case_file.parent),
        loadHFP=False,
        verbose=False,
        logstreams=[StringIO(), StringIO()],
    )

    plan.solve(plan.objective, plan.solverOptions)

    assert plan.caseStatus == "solved"

    return plan


def test_metrics_json_write_and_structure(tmp_path):
    """
    Full workflow test
    """

    content = CONTENT
    case_file = tmp_path / "case_metrics.toml"
    case_file.write_text(content.strip())

    plan = _build_and_solve_plan(case_file)

    metrics_file = tmp_path / "metrics.json"

    write_metrics_json(
        plan,
        metrics_file,
        timing={"elapsed_seconds": 1.0},
    )

    assert metrics_file.exists()

    data = json.loads(metrics_file.read_text())

    assert data["schema"] == "roost.metrics.v2"
    assert "financial" in data
    assert "complexity" in data
    assert "risk" in data
    assert "timing" in data
    assert "run_status" in data

    assert data["run_status"]["status"] == "solved"


def test_metrics_financial_invariants(tmp_path):
    content = CONTENT

    case_file = tmp_path / "case_metrics.toml"
    case_file.write_text(content.strip())

    plan = _build_and_solve_plan(case_file)

    metrics_file = tmp_path / "metrics.json"

    write_metrics_json(plan, metrics_file, timing={})

    data = json.loads(metrics_file.read_text())
    f = data["financial"]

    spending = f["spending"]["total"]
    bequest = f["bequest"]["total"]

    assert spending["future"] >= spending["today"]
    assert bequest["future"] >= bequest["today"]

    gamma = f["inflation"]["final_factor"]

    if gamma > 0:
        approx = bequest["future"] / gamma
        assert abs(approx - bequest["today"]) / max(1.0, bequest["today"]) < 0.02


def test_metrics_robustness_fields(tmp_path):
    content = CONTENT

    case_file = tmp_path / "case_metrics.toml"
    case_file.write_text(content.strip())

    plan = _build_and_solve_plan(case_file)

    metrics_file = tmp_path / "metrics.json"

    write_metrics_json(plan, metrics_file, timing={})

    data = json.loads(metrics_file.read_text())

    risk = data["risk"]["outcome"]
    assets = risk["assets"]

    assert "final_today" in assets
    assert "max_today" in assets
    assert "min_today" in assets


def test_metrics_timeseries_alignment(tmp_path):
    content = CONTENT

    case_file = tmp_path / "case_metrics.toml"
    case_file.write_text(content.strip())

    plan = _build_and_solve_plan(case_file)

    metrics_file = tmp_path / "metrics.json"

    write_metrics_json(plan, metrics_file, timing={})

    data = json.loads(metrics_file.read_text())
    f = data["financial"]

    ts = f["timeseries"]

    gamma = ts["inflation"]["factor_by_year"]
    assets_today = ts["assets"]["today_by_year"]
    assets_future = ts["assets"]["future_by_year"]

    n = len(gamma)

    assert len(assets_today) == n
    assert len(assets_future) == n
