from rich import box
from rich.table import Table


def format_value(value):
    if value is None:
        return "-"

    if isinstance(value, float):
        return f"{value:,.2f}"

    return str(value)


def render_trial(console, row: dict, specs):
    table = Table(
        box=box.SIMPLE,
        show_header=True,
        header_style="bold cyan",
        show_edge=False,
    )

    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    for spec in specs:
        val = row.get(spec.key)
        table.add_row(spec.label, format_value(val))

    console.print(table)


def render_run(console, rows: list[dict], specs):
    table = Table(
        box=box.SIMPLE,
        show_header=True,
        header_style="bold cyan",
        show_edge=False,
    )

    table.add_column("ID", justify="right")

    for spec in specs:
        table.add_column(spec.label, justify=spec.align)

    for i, row in enumerate(rows):
        values = [str(i)]

        for spec in specs:
            val = row.get(spec.key)
            values.append(format_value(val))

        table.add_row(*values)

    console.print(table)
