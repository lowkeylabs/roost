# src/owlroost/domain/services/renderers/rich_table.py

from rich import box
from rich.table import Table


# =========================================================
# Shared helpers
# =========================================================
def _extract(cell):
    """
    Extract formatted value from cell.

    Supports:
        {"value": ..., "formatted": ...}
        or raw values
    """
    if isinstance(cell, dict):
        return cell.get("formatted")
    return cell


def _make_table():
    return Table(
        box=box.SIMPLE_HEAD,
        show_edge=False,
        show_lines=False,
        expand=False,
        pad_edge=False,
    )


def _is_separator(rm):
    return (isinstance(rm, dict) and "separator" in rm) or getattr(rm, "is_separator", False)


def _get_sep_label(rm):
    if isinstance(rm, dict):
        return rm.get("separator_label", "") or ""
    return getattr(rm, "separator_label", "") or ""


# =========================================================
# Table renderer (row-wise)
# =========================================================
def _render_table(console, table):
    rich = _make_table()

    align_map = table.meta.get("align", {})
    wrap_map = table.meta.get("wrap", {})

    # Use stable keys if available
    column_keys = table.meta.get("column_keys", table.columns)

    visible_cols = [i for i, col in enumerate(table.columns) if col != "run_label"]

    for i in visible_cols:
        col_name = table.columns[i]  # display (may include \n)
        col_key = column_keys[i]  # stable lookup key

        if col_name == "ID":
            justify = "right"
            width = None
        else:
            justify = align_map.get(col_key, "right")
            width = wrap_map.get(col_key)

        rich.add_column(
            str(col_name),
            justify=justify,
            width=width,
            no_wrap=False if width else True,
            overflow="fold",
        )

    for row in table.rows:
        visible_row = [row[i] for i in visible_cols]
        rich.add_row(*[str(_extract(c)) for c in visible_row])

    console.print(rich)


# =========================================================
# Pivot renderer (metric-wise)
# =========================================================


def _render_pivot(console, table):
    rich = _make_table()

    align_map = table.meta.get("align", {})
    column_keys = table.meta.get("column_keys", table.columns)

    row_keys = table.meta.get("row_keys", [])
    row_wrap = table.meta.get("row_wrap", {})
    explain = table.meta.get("explain") or set()
    rms = table.meta.get("rms", [])
    rows_data = table.meta.get("rows", [])

    def normalize(label):
        return str(label).replace("\n", " ").strip()

    def extract_str(cell):
        val = _extract(cell)
        return str(val) if val is not None else ""

    # ----------------------------------------
    # Column 0: Metric labels (no wrap)
    # ----------------------------------------
    rich.add_column(
        normalize(table.columns[0]),
        justify="left",
        no_wrap=True,
        overflow="ellipsis",
    )

    # ----------------------------------------
    # Run columns
    # ----------------------------------------
    for i in range(1, len(table.columns)):
        col_name = table.columns[i]
        col_key = column_keys[i]

        justify = align_map.get(col_key, "right")

        rich.add_column(
            normalize(col_name),
            justify=justify,
            no_wrap=False,
            overflow="fold",
        )

    # ----------------------------------------
    # Explanation column (optional)
    # ----------------------------------------
    if explain:
        rich.add_column("Explanation", justify="left")

    # ----------------------------------------
    # Rows
    # ----------------------------------------
    from textwrap import fill

    from owlroost.domain.metrics.metric_spec import explain_metric_series

    for idx, rm in enumerate(rms):
        row = table.rows[idx]

        # ----------------------------------------
        # Separator row (FIXED)
        # ----------------------------------------
        if row_keys[idx] is None:
            label = normalize(_get_sep_label(rm))
            label = f"[bold]{label}[/bold]" if label else ""

            n_cols = 1 + (len(table.columns) - 1) + (1 if explain else 0)

            rich.add_row("", *([""] * (n_cols - 1)))  # blank row
            rich.add_row(label, *([""] * (n_cols - 1)))
            continue

        # ----------------------------------------
        # Metric row
        # ----------------------------------------
        label = normalize(row[0])

        row_key = row_keys[idx] if idx < len(row_keys) else None
        wrap_width = row_wrap.get(row_key)

        # Values
        if wrap_width:
            rest = [fill(extract_str(c), width=wrap_width) for c in row[1:]]
        else:
            rest = [extract_str(c) for c in row[1:]]

        # Explanation
        if explain:
            explanation = explain_metric_series(rm, rows_data, explain)
            rest.append(explanation)

        rich.add_row(label, *rest)

    console.print(rich)


# =========================================================
# Main entry point
# =========================================================
def render_rich_table(console, table):
    """
    Render a RoostTable using Rich.

    Supports:
        - layout = "table"
        - layout = "pivot"
    """

    if not table or not table.columns:
        console.print("[yellow]No data[/yellow]")
        return

    if table.layout == "pivot":
        return _render_pivot(console, table)
    else:
        return _render_table(console, table)
