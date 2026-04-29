# src/owlroost/cli/_main.py

import click

from ..version import __version__


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="owlroost")
@click.pass_context
def cli(ctx):
    """OWL-ROOST v2 CLI (in development).

    documentation in owlroost/cli/_main.py

    """
    pass


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
