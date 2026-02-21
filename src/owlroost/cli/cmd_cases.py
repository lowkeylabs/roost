from pathlib import Path

import click
from loguru import logger

from owlroost.cli.utils import (
    find_case_files,
    index_case_files,
    print_case_list,
    resolve_case_selector,
)
from owlroost.domain.case import Case

# ======================================================================
# Main command
# ======================================================================


@click.command(name="cases")
@click.argument(
    "selector",
    nargs=-1,
)
def cmd_cases(selector):
    """
    List ROOST case files, display a single case, or compare cases.
    """

    directory = Path(".")
    logger.debug(f"Scanning directory: {directory}")

    files = find_case_files(directory)

    if not files:
        click.echo("No .toml case files found.")
        return

    indexed_files = index_case_files(files)

    # ------------------------------------------------------------
    # Comparison mode (2+ selectors)
    # ------------------------------------------------------------
    if len(selector) >= 2:
        paths: list[Path] = []

        for sel in selector:
            match = resolve_case_selector(sel, indexed_files)
            if not match:
                click.echo(f"No case matching '{sel}'")
                return
            paths.append(match)

        _display_case_compare(paths)
        return

    # ------------------------------------------------------------
    # Single selector → display case
    # ------------------------------------------------------------
    if len(selector) == 1:
        match = resolve_case_selector(selector[0], indexed_files)
        if not match:
            click.echo(f"No case matching '{selector[0]}'")
            return

        _display_case(match)
        return

    # ------------------------------------------------------------
    # No selector → list all cases
    # ------------------------------------------------------------
    print_case_list(directory)


# ======================================================================
# Single-case display (Domain-based)
# ======================================================================


def _display_case(path: Path):
    try:
        case = Case(path)
    except Exception as e:
        click.echo(f"Failed to load {path}: {e}")
        return

    config = case.config

    click.echo(f"CASE FILE : {path.name}")
    click.echo(f"CASE NAME : {case.name}")
    click.echo("-" * 80)

    # ------------------------------------------------------------
    # Description
    # ------------------------------------------------------------
    if config.description:
        click.echo("DESCRIPTION")
        click.echo(config.description)
        click.echo()

    # ------------------------------------------------------------
    # Household
    # ------------------------------------------------------------
    basic = config.basic_info

    click.echo("HOUSEHOLD")
    click.echo(f"  Members        : {', '.join(basic.names)}")
    click.echo(f"  Status         : {basic.status}")

    if basic.date_of_birth:
        click.echo(f"  Birth dates    : {', '.join(basic.date_of_birth)}")

    click.echo(f"  Life expectancy: {', '.join(map(str, basic.life_expectancy))}")
    click.echo(f"  Start date     : {basic.start_date}")
    click.echo()

    # ------------------------------------------------------------
    # Assets
    # ------------------------------------------------------------
    click.echo("ASSETS (balances)")
    click.echo(f"  Taxable        : {case.taxable_assets}")
    click.echo(f"  Tax-deferred   : {case.tax_deferred_assets}")
    click.echo(f"  Tax-free       : {case.tax_free_assets}")
    click.echo()

    # ------------------------------------------------------------
    # HFP
    # ------------------------------------------------------------
    hfp = config.household_financial_profile
    if hfp and hfp.HFP_file_name:
        click.echo("HOUSEHOLD FINANCIAL PROFILE")
        click.echo(f"  HFP file       : {hfp.HFP_file_name}")
        click.echo()

    # ------------------------------------------------------------
    # Fixed Income
    # ------------------------------------------------------------
    fixed = config.fixed_income

    if fixed.pension_monthly_amounts or fixed.social_security_pia_amounts:
        click.echo("FIXED INCOME")

        if fixed.pension_monthly_amounts:
            click.echo(
                f"  Pensions (monthly): " f"{', '.join(map(str, fixed.pension_monthly_amounts))}"
            )

        if fixed.social_security_pia_amounts:
            click.echo(
                f"  Social Security PIA: "
                f"{', '.join(map(str, fixed.social_security_pia_amounts))}"
            )

        click.echo()

    # ------------------------------------------------------------
    # Rates
    # ------------------------------------------------------------
    rates = config.rates_selection

    if rates.method:
        click.echo("RATES")
        click.echo(f"  Method         : {rates.method}")

        if rates.from_ is not None and rates.to is not None:
            click.echo(f"  Window         : {rates.from_}–{rates.to}")

        click.echo()

    # ------------------------------------------------------------
    # Asset Allocation
    # ------------------------------------------------------------
    alloc = config.asset_allocation

    click.echo("ASSET ALLOCATION")
    click.echo(f"  Type           : {alloc.type}")
    click.echo(f"  Interpolation  : {alloc.interpolation_method}")
    click.echo()

    # ------------------------------------------------------------
    # Optimization
    # ------------------------------------------------------------
    opt = config.optimization_parameters
    solver = config.solver_options or {}

    click.echo("OPTIMIZATION")
    click.echo(f"  Objective      : {opt.objective}")
    click.echo(f"  Spending model : {opt.spending_profile}")
    click.echo(f"  Survivor spend : {opt.surviving_spouse_spending_percent}%")

    if opt.objective == "maxSpending" and solver.get("bequest") is not None:
        click.echo(f"  Target         : bequest = {solver['bequest']}")

    if opt.objective == "maxBequest" and solver.get("netSpending") is not None:
        click.echo(f"  Target         : netSpending = {solver['netSpending']}")

    click.echo()

    # ------------------------------------------------------------
    # Solver / Roth
    # ------------------------------------------------------------
    click.echo("SOLVER / ROTH POLICY")

    if solver.get("solver"):
        click.echo(f"  Engine              : {solver['solver']}")

    no_roth = solver.get("noRothConversions")

    if no_roth == "None":
        click.echo("  Roth excluded       : no one excluded")
    elif isinstance(no_roth, list) and no_roth:
        click.echo(f"  Roth excluded       : {', '.join(map(str, no_roth))}")
    else:
        click.echo("  Roth excluded       : (not specified)")

    if solver.get("startRothConversions") is not None:
        click.echo(f"  Roth start year     : {solver['startRothConversions']}")

    if solver.get("maxRothConversion") is not None:
        click.echo(f"  Max Roth conversion : {solver['maxRothConversion']}")

    if solver.get("spendingSlack"):
        click.echo(f"  Spending slack      : {solver['spendingSlack']}")

    if solver.get("withMedicare"):
        click.echo(f"  Medicare modeling   : {solver['withMedicare']}")

    click.echo()


# ======================================================================
# Comparison display (Domain-based)
# ======================================================================


def _display_case_compare(paths: list[Path]):
    try:
        cases = [Case(p) for p in paths]
    except Exception as e:
        click.echo(f"Failed to load cases: {e}")
        return

    col_width = 22
    label_width = 30

    header = f"{'':<{label_width}}"
    for case in cases:
        header += f"{case.name[:col_width]:<{col_width}}"

    click.echo(header)
    click.echo("-" * (label_width + col_width * len(cases)))

    def row(label, extractor):
        line = f"{label:<{label_width}}"
        for case in cases:
            try:
                val = extractor(case)
                if isinstance(val, list):
                    val = ", ".join(map(str, val))
                val = "." if val is None else str(val)
            except Exception:
                val = "."
            line += f"{val[:col_width]:<{col_width}}"
        click.echo(line)

    row("CASE NAME", lambda c: c.name)
    row("HOUSEHOLD NAMES", lambda c: ", ".join(c.household_names))
    row("START DATE", lambda c: c.start_date)
    row("TAXABLE ASSETS", lambda c: c.taxable_assets)
    row("TAX-DEFERRED ASSETS", lambda c: c.tax_deferred_assets)
    row("TAX-FREE ASSETS", lambda c: c.tax_free_assets)
    row("OPT OBJECTIVE", lambda c: c.objective)
    row("SOLVER", lambda c: c.config.solver_options.get("solver"))
