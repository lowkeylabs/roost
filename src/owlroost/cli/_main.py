import os

import click

from owlroost.core.configure_logging import LOG_LEVELS, configure_logging
from owlroost.core.solver_info import get_owl_solver_info
from owlroost.version import __version__

from .cmd_audit import cmd_audit
from .cmd_cases import cmd_cases
from .cmd_inspect import cmd_inspect
from .cmd_results import cmd_results
from .cmd_run import cmd_run
from .cmd_summarize import cmd_summarize

early_level = os.getenv("OWLSTATION_LOG_LEVEL", "INFO")
if early_level:
    early_level = early_level.upper()
if early_level in LOG_LEVELS:
    configure_logging(early_level)


@click.group(invoke_without_command=True)
@click.option(
    "--log-level",
    type=click.Choice(LOG_LEVELS, case_sensitive=False),
    default=None,
    help="Set logging verbosity.",
)
@click.version_option(version=__version__, prog_name="owlroost")
@click.pass_context
def cli(ctx, log_level: str | None):
    """ROOST - Retirement Options and Outcomes Studies Toolkit

    Examples:

    \b
    roost cases                       <- show all case/TOML files in current directory
    roost run Case_jack+jill.toml     <- run a case
    roost run 0                       <- run a case by its ID from 'roost cases' or 'roost run'
    roost run 0 longevity.values.0=99 <- run OWL on case ID 0, first setting longevity for person 0 to 99
    roost results                     <- show results of all runs for all cases in ./results
    roost results jack+jill           <- show results for case 'jack+jill'
    roost results 0                   <- show results for case ID 0 from 'roost results'
    roost results 0 0                 <- show results for run ID 0 of case ID 0 from 'roost results'
    roost results 0 0 --summary       <- show summary of run ID 0 of case ID 0 from 'roost results'
    roost results 0 0 --original      <- show original TOML case file ...
    roost results 0 0 --effective     <- show effective TOML case file ...
    """
    ctx.ensure_object(dict)

    configure_logging(log_level)

    overrides = []
    if log_level:
        overrides.append(f"logging.level={log_level}")

    #    cfg = load_hydra_config(overrides)
    #    hc = HydraConfig.get()
    #    logger.debug("Hydra configuration sources (in precedence order):")
    #    for src in hc.runtime.config_sources:
    #        logger.debug(f"  - {src.provider}: {src.path}")

    #    ctx.obj["cfg"] = cfg

    #    configure_logging(cfg.logging.level)

    #    logger.debug(f"Resolved logging configuration:\n{OmegaConf.to_yaml(cfg.logging, resolve=True)}")

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


cli.add_command(cmd_cases)
cli.add_command(cmd_run)
cli.add_command(cmd_results)
cli.add_command(cmd_audit)
cli.add_command(cmd_summarize)
cli.add_command(cmd_inspect)


@cli.command()
@click.pass_context
def info(ctx):
    """Show OWL-Station and OWL solver version information."""
    solver = get_owl_solver_info()

    click.echo(f"OWL-ROOST version: {__version__}")
    click.echo(f"OWL-Planner version: {solver.version}")

    if solver.commit:
        click.echo(f"OWL-Planner commit:  {solver.commit}")

    click.echo(f"{solver}")
