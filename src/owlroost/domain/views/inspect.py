from rich import box
from rich.table import Table

from owlroost.domain.formatting import format_value


def get_row_value(row: dict, rm):
    """
    Resolve correct key based on aggregate.
    """
    if rm.aggregate:
        return row.get(f"{rm.key}_{rm.aggregate}")
    return row.get(rm.key)


# =========================================================
# Trial View
# =========================================================


def render_trial(console, row: dict, specs):
    table = Table(
        box=box.SIMPLE,
        show_header=True,
        header_style="bold cyan",
        show_edge=False,
    )

    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    for rm in specs:
        val = get_row_value(row, rm)
        table.add_row(rm.label, format_value(val, rm.fmt))

    console.print(table)


# =========================================================
# Run View
# =========================================================


def render_run(console, rows: list[dict], specs):
    table = Table(
        box=box.SIMPLE,
        show_header=True,
        header_style="bold cyan",
        show_edge=False,
    )

    table.add_column("ID", justify="right")

    for rm in specs:
        table.add_column(rm.label, justify=rm.align)

    for i, row in enumerate(rows):
        values = [str(i)]

        for rm in specs:
            val = get_row_value(row, rm)
            values.append(format_value(val, rm.fmt))

        table.add_row(*values)

    console.print(table)
