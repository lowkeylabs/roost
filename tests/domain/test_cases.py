from pathlib import Path

import pytest

from owlroost.core.case_upgrade import case_upgrade
from owlroost.domain.models.case import Case, LongevityConfig, RoostConfig

# =========================================================
# Test Fixture Helper
# =========================================================


def write_case(tmp_path: Path, names: list[str]) -> Path:
    """
    Generate a minimal but schema-valid OWL case
    parameterized by household names.
    """

    n = len(names)

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

    generic_block = ", ".join("[[60,40,0,0],[60,40,0,0]]" for _ in names)

    content = f"""
case_name = "{'+'.join(names)}"

[basic_info]
status = "single"
names = [{name_entries}]
date_of_birth = [{dob_entries}]
life_expectancy = [{life_entries}]
start_date = "2025-01-01"

[savings_assets]
taxable_savings_balances = [{taxable}]
tax_deferred_savings_balances = [{tax_deferred}]
tax_free_savings_balances = [{tax_free}]
beneficiary_fractions = {[1.0] * (2*n - 1)}
spousal_surplus_deposit_fraction = 0.5

[household_financial_profile]
HFP_file_name = "dummy.xlsx"

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
objective = "maxSpending"

[solver_options]
solver = "HiGHS"

[results]
default_plots = "today"
"""

    file = tmp_path / "case_test.toml"
    file.write_text(content.strip())
    return file


# =========================================================
# LongevityConfig Unit Tests
# =========================================================


def test_longevity_defaults():
    cfg = LongevityConfig()

    assert cfg.lifetime_percentile == [0.80]
    assert cfg.sex == ["female"]
    assert cfg.health == ["average"]
    assert cfg.smoker == [False]
    assert cfg.partnered is True


def test_lifetime_percentile_validation():
    with pytest.raises(ValueError):
        LongevityConfig(lifetime_percentile=[0.0])

    with pytest.raises(ValueError):
        LongevityConfig(lifetime_percentile=[1.5])

    with pytest.raises(ValueError):
        LongevityConfig(lifetime_percentile=[])


def test_health_coercion():
    cfg = LongevityConfig(health="excellent")
    assert cfg.health == ["excellent"]


def test_smoker_coercion():
    cfg = LongevityConfig(smoker=True)
    assert cfg.smoker == [True]


# =========================================================
# RoostConfig Tests
# =========================================================


def test_roost_defaults():
    cfg = RoostConfig()
    assert isinstance(cfg.master_seed, int)
    assert cfg.trials == 1


# =========================================================
# Case Domain Tests
# =========================================================


def test_case_basic_properties(tmp_path):
    case_file = write_case(tmp_path, ["Alice", "Bob"])
    case = Case(case_file)

    assert case.household_names == ["Alice", "Bob"]
    assert case.start_year == 2025
    assert case.total_savings == 700.0  # 100+200+50 per person


def test_longevity_alignment_truncates(tmp_path):
    case_file = write_case(tmp_path, ["Alice"])

    # Inject oversized longevity vector
    content = (
        case_file.read_text()
        + """

[longevity]
lifetime_percentile = [0.8, 0.9]
sex = ["female"]
health = ["average"]
smoker = [false]
partnered = true
"""
    )
    case_file.write_text(content)

    case = Case(case_file)

    assert case.longevity is not None
    assert len(case.longevity.lifetime_percentile) == 1
    assert len(case.longevity.sex) == 1
    assert len(case.longevity.health) == 1
    assert len(case.longevity.smoker) == 1


def test_longevity_alignment_pads(tmp_path):
    case_file = write_case(tmp_path, ["Alice", "Bob"])

    content = (
        case_file.read_text()
        + """

[longevity]
lifetime_percentile = [0.6]
sex = ["female"]
health = ["average"]
smoker = [false]
partnered = false
"""
    )
    case_file.write_text(content)

    case = Case(case_file)

    assert case.longevity is not None
    assert len(case.longevity.lifetime_percentile) == 2
    assert len(case.longevity.sex) == 2
    assert len(case.longevity.health) == 2
    assert len(case.longevity.smoker) == 2


def test_deterministic_life_ages_empty_without_longevity(tmp_path):
    case_file = write_case(tmp_path, ["Alice"])
    case = Case(case_file)

    assert case.deterministic_life_ages == []


def test_deterministic_life_ages_single_person(tmp_path):
    case_file = write_case(tmp_path, ["Alice"])

    content = (
        case_file.read_text()
        + """

[longevity]
lifetime_percentile = [0.6]
sex = ["female"]
health = ["average"]
smoker = [false]
partnered = false
"""
    )
    case_file.write_text(content)

    case = Case(case_file)

    ages = case.deterministic_life_ages
    assert len(ages) == 1
    assert ages[0] >= case.ages[0]


def test_deterministic_last_survivor(tmp_path):
    case_file = write_case(tmp_path, ["Alice", "Bob"])

    content = (
        case_file.read_text()
        + """

[longevity]
lifetime_percentile = [0.6, 0.7]
sex = ["female", "male"]
health = ["average", "average"]
smoker = [false, false]
partnered = true
"""
    )
    case_file.write_text(content)

    case = Case(case_file)

    last = case.deterministic_last_survivor_age
    assert last is not None
    assert last >= max(case.ages)


def test_professional_summary_contains_names(tmp_path):
    case_file = write_case(tmp_path, ["Alice", "Bob"])
    case = Case(case_file)

    summary = case.professional_summary

    assert isinstance(summary, str)
    for name in case.household_names:
        assert name in summary
    assert str(case.start_year) in summary


# =========================================================
# Structural Lever (v1) Tests
# =========================================================


def test_conversion_lever_present(tmp_path):
    case_file = write_case(tmp_path, ["Alice"])
    case = Case(case_file)

    # default fixture: tax-deferred and tax-free both > 0
    assert case.has_conversion_lever is True


def test_ss_lever_present_when_pia_positive(tmp_path):
    case_file = write_case(tmp_path, ["Alice"])

    content = case_file.read_text().replace(
        "social_security_pia_amounts = [0]",
        "social_security_pia_amounts = [2000]",
    )
    case_file.write_text(content)

    case = Case(case_file)

    assert case.has_ss_lever is True


def test_ss_lever_absent_when_pia_zero(tmp_path):
    case_file = write_case(tmp_path, ["Alice"])
    case = Case(case_file)

    assert case.has_ss_lever is False


def test_allocation_lever_present(tmp_path):
    case_file = write_case(tmp_path, ["Alice"])
    case = Case(case_file)

    assert case.has_allocation_lever is True


def test_pre_tax_share_computation(tmp_path):
    case_file = write_case(tmp_path, ["Alice"])
    case = Case(case_file)

    expected = 200.0 / (100.0 + 200.0 + 50.0)
    assert case.pre_tax_share == expected


def test_equity_share_from_allocation(tmp_path):
    case_file = write_case(tmp_path, ["Alice"])
    case = Case(case_file)

    # allocation = [60,40,0,0]
    assert case.equity_share == 0.60


def test_funded_ratio_zero_if_no_spending_defined(tmp_path):
    case_file = write_case(tmp_path, ["Alice"])
    case = Case(case_file)

    # fixture does not define explicit spending
    assert case.funded_ratio == 0.0


def test_rates_selection_from_roundtrip_via_case_write(tmp_path):
    """
    Ensure that 'from' in [rates_selection] is not rewritten
    as 'from_' when Case.write() is called.
    """

    case_file = write_case(tmp_path, ["Alice"])

    # Ensure fixture uses a historical method with from/to
    content = case_file.read_text().replace(
        'method = "user"',
        'method = "historical"',
    )
    case_file.write_text(content)

    case = Case(case_file)

    # Trigger write
    case.write()

    written = case_file.read_text()

    assert "from =" in written
    assert "from_ =" not in written


def test_rates_selection_from_roundtrip_via_case_upgrade(tmp_path):
    """
    Ensure that case_upgrade(write=True) does not rewrite
    'from' as 'from_'.
    """

    case_file = write_case(tmp_path, ["Alice"])

    content = case_file.read_text().replace(
        'method = "user"',
        'method = "historical"',
    )
    case_file.write_text(content)

    case = Case(case_file)

    # Upgrade and write
    case_upgrade(case, write=True)

    written = case_file.read_text()

    assert "from =" in written
    assert "from_ =" not in written
