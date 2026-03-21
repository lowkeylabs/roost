from rich import box
from rich.table import Table

from owlroost.domain.formatting import format_value
from owlroost.domain.metrics.metric_spec import explain_metric_series, resolve_metric_value


# =========================================================
# Shared value resolver
# =========================================================
def get_value(row, rm):
    val = resolve_metric_value(row, rm.key, getattr(rm, "aggregate", None))
    return format_value(val, rm.spec.fmt)


# =========================================================
# Main dispatcher
# =========================================================
def render_table(console, rows, view, layout="table", explain=False):
    if layout == "pivot":
        return render_pivot_table(console, rows, view, explain=explain)
    else:
        return render_standard_table(console, rows, view, explain=explain)

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
def render_standard_table(console, rows, view, explain=False):
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

    # explanation row after all rows are rendered.
    # After all rows rendered

    if explain:
        explanation_row = [""]  # for ID column

        for rm in view:
            explanation = explain_metric_series(rm, rows)
            explanation_row.append(explanation)

        table.add_row(*explanation_row, style="dim")

    console.print(table)


# =========================================================
# Pivot table (metrics as rows)
# =========================================================
def render_pivot_table(console, rows, view, explain=False):
    if rows is None:
        console.print("[yellow]No data[/yellow]")
        return

    # Normalize single row
    if isinstance(rows, dict):
        rows = [rows]

    if not rows:
        console.print("[yellow]No data[/yellow]")
        return

    # ----------------------------------------
    # Build table
    # ----------------------------------------
    table = make_table()

    # First column = metric labels
    table.add_column("Metric", justify="left")

    # One column per row (run/trial)
    for i, _row in enumerate(rows):
        table.add_column(str(i), justify="right")

    # NEW: Explanation column
    if explain:
        table.add_column("Explanation", justify="left")

    # ----------------------------------------
    # Each metric becomes a row
    # ----------------------------------------
    for rm in view:
        # Label
        label = rm.spec.label or rm.spec.key
        if getattr(rm, "aggregate", None):
            label = f"{label} ({rm.aggregate})"

        row_cells = [label]

        # Values
        for r in rows:
            formatted = get_value(r, rm)
            row_cells.append(formatted)

        # Explanation (series-aware)
        if explain:
            explanation = explain_metric_series(rm, rows)
            row_cells.append(explanation)

        table.add_row(*row_cells)

    console.print(table)
