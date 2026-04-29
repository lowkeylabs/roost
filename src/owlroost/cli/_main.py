# src/owlroost/cli/_main.py

import click


@click.group()
def cli():
    """OWL-ROOST v2 CLI (in development)."""
    pass


@cli.command()
def version():
    """Show version."""
    print("owlroost v2 (in development)")
