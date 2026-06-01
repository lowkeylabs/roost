# src/owlroost/cli/cmd_schema.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

import click

from owlroost.schema.bootstrap import build_registry


# ---------------------------------------------------------
# Root command group
# ---------------------------------------------------------
@click.group(name="schema")
def cmd_schema():
    """Inspect schema registry."""
    pass


# ---------------------------------------------------------
# schema list
# ---------------------------------------------------------
@cmd_schema.command("list")
def list_fields():
    """List all schema fields."""
    reg = build_registry()

    for field in sorted(reg.all(), key=lambda f: f.name):
        click.echo(field.name)


# ---------------------------------------------------------
# schema show <field>
# ---------------------------------------------------------
@cmd_schema.command("show")
@click.argument("name")
def show_field(name):
    """Show details for a specific field."""
    reg = build_registry()

    try:
        field = reg.get(name)
    except KeyError as err:
        raise click.ClickException(f"Unknown field: {name}") from err

    click.echo(f"Name       : {field.name}")
    click.echo(f"Type       : {getattr(field.dtype, '__name__', str(field.dtype))}")
    click.echo(f"Source     : {field.source}")
    click.echo(f"Path       : {field.path}")
    click.echo(f"Aggregates : {field.aggregates}")
    click.echo(f"Description: {field.description}")


# ---------------------------------------------------------
# schema find <pattern>
# ---------------------------------------------------------
@cmd_schema.command("find")
@click.argument("pattern")
def find_fields(pattern):
    """Search for fields by substring."""
    reg = build_registry()

    pattern = pattern.lower()

    for field in reg.all():
        if pattern in field.name.lower():
            click.echo(field.name)


# ---------------------------------------------------------
# schema tree
# ---------------------------------------------------------
@cmd_schema.command("tree")
def tree():
    """Display schema as a tree."""
    reg = build_registry()

    tree = {}

    # Build nested dict
    for field in reg.all():
        cur = tree
        for part in field.name.split("."):
            cur = cur.setdefault(part, {})

    # Recursive printer
    def print_tree(node, prefix=""):
        for key, child in sorted(node.items()):
            click.echo(prefix + key)
            print_tree(child, prefix + "  ")

    print_tree(tree)
