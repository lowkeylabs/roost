from rich import box
from rich.table import Table

from owlroost.domain.formatting import format_value


# =========================================================
# Shared value resolver
# =========================================================
def get_value(row, rm):
    lookup_key = rm.key

    # Handle aggregate metrics
    if getattr(rm, "aggregate", None):
        agg_key = f"{rm.key}_{rm.aggregate}"
        if agg_key in row:
            lookup_key = agg_key

    val = row.get(lookup_key)
    return format_value(val, rm.spec.fmt)


# =========================================================
# Main dispatcher
# =========================================================
def render_table(console, rows, view, layout="table"):
    if layout == "pivot":
        return render_pivot_table(console, rows, view)
    else:
        return render_standard_table(console, rows, view)

    return


# =========================================================
# Shared table factory
# =========================================================
def make_table():
    return Table(
        box=box.SIMPLE_HEAD,  # ← single header line, no outer border
        show_edge=False,
        show_lines=False,
        expand=False,
        pad_edge=False,
    )


# =========================================================
# Standard table (row-wise)
# =========================================================
def render_standard_table(console, rows, view):
    if rows is None:
        console.print("[yellow]No data[/yellow]")
        return

    # Normalize single row
    if isinstance(rows, dict):
        rows = [rows]

    if not rows:
        console.print("[yellow]No data[/yellow]")
        return

    table = make_table()

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
            formatted = get_value(row, rm)
            values.append(formatted)

        table.add_row(*values)

    console.print(table)


# =========================================================
# Pivot table (metrics as rows)
# =========================================================
def render_pivot_table(console, rows, view):
    if rows is None:
        console.print("[yellow]No data[/yellow]")
        return

    # Normalize single row
    if isinstance(rows, dict):
        rows = [rows]

    if not rows:
        console.print("[yellow]No data[/yellow]")
        return

    table = make_table()

    # ----------------------------------------
    # First column = metric labels
    # ----------------------------------------
    table.add_column("Metric", justify="left")

    # ----------------------------------------
    # One column per row (run/trial)
    # ----------------------------------------
    for i, _row in enumerate(rows):
        label = str(i)
        table.add_column(label, justify="right")

    # ----------------------------------------
    # Each metric becomes a row
    # ----------------------------------------
    for rm in view:
        # Clean label (avoid multi-line issues)
        label = rm.spec.label or rm.spec.key
        if getattr(rm, "aggregate", None):
            label = f"{label} ({rm.aggregate})"

        row_cells = [label]

        for r in rows:
            formatted = get_value(r, rm)
            row_cells.append(formatted)

        table.add_row(*row_cells)

    console.print(table)
