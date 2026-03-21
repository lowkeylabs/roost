from rich.table import Table

from owlroost.domain.formatting import format_value


def render_rows(console, rows, view):
    if rows is None:
        console.print("[yellow]No data[/yellow]")
        return

    # Normalize single row
    if isinstance(rows, dict):
        rows = [rows]

    if not rows:
        console.print("[yellow]No data[/yellow]")
        return

    table = Table()

    # -----------------------------------------------------
    # Columns
    # -----------------------------------------------------
    table.add_column("ID", justify="right")

    for rm in view:
        label = rm.spec.label or rm.spec.key
        table.add_column(label, justify=rm.spec.align or "right")

    # -----------------------------------------------------
    # Rows
    # -----------------------------------------------------
    for i, row in enumerate(rows):
        values = [str(i)]

        for rm in view:
            lookup_key = rm.key

            if getattr(rm, "aggregate", None):
                agg_key = f"{rm.key}_{rm.aggregate}"
                if agg_key in row:
                    lookup_key = agg_key

            val = row.get(lookup_key)
            formatted = format_value(val, rm.spec.fmt)
            values.append(formatted)

        table.add_row(*values)

    console.print(table)
