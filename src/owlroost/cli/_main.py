# src/owlroost/cli/_main.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

import sys

import click
from loguru import logger

from ..version import __version__
from .cmd_build import cmd_build
from .cmd_reports import cmd_reports
from .cmd_results import cmd_results
from .cmd_run import cmd_run
from .cmd_vars import cmd_vars


@click.group(invoke_without_command=True)
@click.version_option(
    version=__version__,
    prog_name="owlroost",
)
@click.option(
    "--log-level",
    default="INFO",
    show_default=True,
    help="Log level",
)
@click.pass_context
def cli(
    ctx,
    log_level,
):
    """
    OWL-ROOST v2 CLI (in development).

    documentation in owlroost/cli/_main.py
    """

    # ----------------------------------------
    # Normalize level
    # ----------------------------------------
    log_level = log_level.upper()

    # ----------------------------------------
    # Reset loguru
    # ----------------------------------------
    logger.remove()
    logger.add(sys.stderr, level=log_level)
    # ----------------------------------------
    # Store on context
    # ----------------------------------------
    ctx.ensure_object(dict)
    ctx.obj["log_level"] = log_level


@cli.command()
@click.pass_context
def info(ctx):
    """Show OWL-Station and OWL solver version information."""
    click.echo(f"OWL-ROOST version: {__version__}")


#    solver = get_owl_solver_info()
#    click.echo(f"OWL-Planner version: {solver.version}")
#    if solver.commit:
#        click.echo(f"OWL-Planner commit:  {solver.commit}")
#    click.echo(f"{solver}")


cli.add_command(cmd_build, name="cases")
cli.add_command(cmd_build, name="build")

cli.add_command(cmd_run)
cli.add_command(cmd_reports)
cli.add_command(cmd_results)
cli.add_command(cmd_vars)
