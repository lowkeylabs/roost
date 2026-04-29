from rich import box
from rich.table import Table

from owlroost.domain.metrics.metric_spec import (
    build_visibility_context,
    explain_metric_series,
    resolve_metric_value,
)


# =========================================================
# Shared value resolver
# =========================================================
def get_value(row, rm, ctx=None):
    val, fmt_override = resolve_metric_value(row, rm.key, getattr(rm, "aggregate", None))

    return rm.spec.render_value(val, row=row, ctx=ctx, fmt_override=fmt_override)


# =========================================================
# Main dispatcher
# =========================================================
def render_table(console, rows, view, layout="table", explain: set[str] | None = None):
    if rows is None:
        return render_standard_table(console, rows, view, explain=explain)

    # Normalize single row early
    if isinstance(rows, dict):
        rows = [rows]

    # ----------------------------------------
    # APPLY show_if filtering (NEW)
    # ----------------------------------------
    ctx = build_visibility_context(rows)

    def view_allows(show_if, layout):
        if show_if is None:
            return True
        if show_if == "is_pivot":
            return layout == "pivot"
        if show_if == "is_table":
            return layout == "table"
        return True

    filtered_view = []

    for rm in view:
        # Skip non-metric entries (separators, etc.)
        if getattr(rm, "spec", None) is None:
            filtered_view.append(rm)  # still keep for pivot rendering
            continue

        if rm.view_show_if and not view_allows(rm.view_show_if, layout):
            continue

        filtered_view.append(rm)

    # ----------------------------------------
    # Deduplicate aggregates for single-row (NEW)
    # ----------------------------------------
    if ctx["is_single"]:
        seen = set()
        deduped = []

        for rm in filtered_view:
            # Skip non-metric entries
            if getattr(rm, "spec", None) is None:
                deduped.append(rm)
                continue

            key = rm.key

            if key in seen:
                continue

            seen.add(key)
            deduped.append(rm)

        filtered_view = deduped

    # ----------------------------------------
    # Dispatch
    # ----------------------------------------

    if layout == "pivot":
        return render_pivot_table(console, rows, filtered_view, ctx=ctx, explain=explain)
    else:
        return render_standard_table(console, rows, filtered_view, ctx=ctx, explain=explain)


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
def render_standard_table(console, rows, view, ctx, explain: set[str] | None = None):
    if rows is None:
        console.print("[yellow]No data[/yellow]")
        return

    # Normalize single row
    if isinstance(rows, dict):
        rows = [rows]

    if not rows:
        console.print("[yellow]No data[/yellow]")
        return

    explain = explain or set()

    table = make_table()

    # -----------------------------------------------------
    # Columns
    # -----------------------------------------------------
    table.add_column("ID", justify="right")

    for rm in view:
        if getattr(rm, "spec", None) is None:
            continue
        label = rm.spec.label or rm.spec.key
        table.add_column(label, justify=rm.spec.align or "right")

    # -----------------------------------------------------
    # Rows
    # -----------------------------------------------------
    for i, row in enumerate(rows):
        values = [str(i)]

        for rm in view:
            if getattr(rm, "spec", None) is None:
                continue
            formatted = get_value(row, rm, ctx)
            values.append(formatted)

        table.add_row(*values)

    # explanation row after all rows are rendered.
    # After all rows rendered

    if explain:
        explanation_row = [""]  # for ID column

        for rm in view:
            if getattr(rm, "spec", None) is None:
                continue
            explanation = explain_metric_series(rm, rows, explain)
            explanation_row.append(explanation)

        table.add_row(*explanation_row, style="dim")

    console.print(table)


# =========================================================
# Pivot table (metrics as rows)
# =========================================================
def render_pivot_table(console, rows, view, ctx, explain: set[str] | None = None):
    if rows is None:
        console.print("[yellow]No data[/yellow]")
        return

    # Normalize single row
    if isinstance(rows, dict):
        rows = [rows]

    if not rows:
        console.print("[yellow]No data[/yellow]")
        return

    explain = explain or set()

    # ----------------------------------------
    # Build table
    # ----------------------------------------
    table = make_table()

    # First column = metric labels
    table.add_column(
        "Metric",
        justify="left",
        min_width=24,  # ← adjust to taste (22–30 works well)
        no_wrap=True,  # ← prevents ugly multi-line metric labels
    )

    # One column per row (run/trial)
    for i, _row in enumerate(rows):
        table.add_column(str(i), justify="right")

    # NEW: Explanation column
    if explain:
        table.add_column("Explanation", justify="left")

    # ----------------------------------------
    # Each metric becomes a row
    # ----------------------------------------
    # rm : resolved metric with all attributes

    for rm in view:
        # ----------------------------------------
        # Separator row
        # ----------------------------------------
        if getattr(rm, "is_separator", False):
            # total columns:
            n_cols = 1 + len(rows) + (1 if explain else 0)

            # ----------------------------------------
            # Always render as blank row (safe)
            # ----------------------------------------
            table.add_row(*([""] * n_cols))

            continue

        # Label

        label = rm.spec.label or rm.spec.key
        agg = getattr(rm, "aggregate", None)

        # Context-aware label
        if label:
            label = label.replace("\n", " ").strip()

        if agg and ctx["is_stochastic"]:
            label = f"{label} ({agg})"

        row_cells = [label]

        # Values
        for r in rows:
            formatted = get_value(r, rm, ctx)
            row_cells.append(formatted)

        # Explanation (series-aware)
        if explain:
            explanation = explain_metric_series(rm, rows, explain)
            row_cells.append(explanation)

        table.add_row(*row_cells)

    console.print(table)
