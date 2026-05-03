# src/owlroost/display/renderers/rich_table.py

from rich.console import Console
from rich.table import Table


def render_rich_table(table):
    rich = Table()

    for col in table.columns:
        rich.add_column(str(col))

    for row in table.rows:
        rich.add_row(*[str(c) for c in row])

    console = Console()
    console.print(rich)

    return ""
