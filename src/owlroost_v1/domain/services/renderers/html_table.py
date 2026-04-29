# src/owlroost/domain/services/renderers/html_table.py

from html import escape
from textwrap import fill


# =========================================================
# Shared helpers (PARITY with rich)
# =========================================================
def _extract(cell):
    if isinstance(cell, dict):
        return cell.get("formatted")
    return cell


def _is_separator(rm):
    return (isinstance(rm, dict) and "separator" in rm) or getattr(rm, "is_separator", False)


def _get_sep_label(rm):
    if isinstance(rm, dict):
        return rm.get("separator_label", "") or ""
    return getattr(rm, "separator_label", "") or ""


def _normalize(label):
    return str(label).replace("\n", " ").strip()


def _style_align(align: str) -> str:
    return f"text-align:{align};"


def _style_wrap(width):
    if not width:
        return ""
    return f"max-width:{width}ch; white-space:normal; word-break:break-word;"


# =========================================================
# TABLE RENDER (row-wise)
# =========================================================
def _render_table(table):
    align_map = table.meta.get("align", {})
    wrap_map = table.meta.get("wrap", {})
    column_keys = table.meta.get("column_keys", table.columns)

    visible_cols = [i for i, col in enumerate(table.columns) if col != "run_label"]

    html = ["<table class='roost-table'>"]

    # ----------------------------------------
    # Header
    # ----------------------------------------
    html.append("<thead><tr>")
    for i in visible_cols:
        col_name = table.columns[i]
        col_key = column_keys[i]

        if col_name == "ID":
            align = "right"
        else:
            align = align_map.get(col_key, "right")

        style = _style_align(align)

        html.append(f"<th style='{style}'>{escape(str(col_name))}</th>")
    html.append("</tr></thead>")

    # ----------------------------------------
    # Body
    # ----------------------------------------
    html.append("<tbody>")
    for row in table.rows:
        html.append("<tr>")
        for i in visible_cols:
            col_key = column_keys[i]
            align = align_map.get(col_key, "right")
            wrap = wrap_map.get(col_key)

            style = _style_align(align) + _style_wrap(wrap)

            val = _extract(row[i])
            val = "" if val is None else str(val)

            html.append(f"<td style='{style}'>{escape(val)}</td>")
        html.append("</tr>")
    html.append("</tbody></table>")

    return "\n".join(html)


# =========================================================
# PIVOT RENDER (metric-wise)
# =========================================================
def _render_pivot(table):
    from owlroost.domain.metrics.metric_spec import explain_metric_series

    align_map = table.meta.get("align", {})
    column_keys = table.meta.get("column_keys", table.columns)

    row_keys = table.meta.get("row_keys", [])
    row_wrap = table.meta.get("row_wrap", {})
    explain = table.meta.get("explain") or set()
    rms = table.meta.get("rms", [])
    rows_data = table.meta.get("rows", [])

    html = ["<table class='roost-table roost-pivot'>"]

    # ----------------------------------------
    # Header
    # ----------------------------------------
    html.append("<thead><tr>")

    # Metric column
    html.append(f"<th style='text-align:left'>{escape(_normalize(table.columns[0]))}</th>")

    # Run columns
    for i in range(1, len(table.columns)):
        col_name = _normalize(table.columns[i])
        col_key = column_keys[i]
        align = align_map.get(col_key, "right")

        html.append(f"<th style='{_style_align(align)}'>{escape(col_name)}</th>")

    if explain:
        html.append("<th style='text-align:left'>Explanation</th>")

    html.append("</tr></thead>")

    # ----------------------------------------
    # Body
    # ----------------------------------------
    html.append("<tbody>")

    for idx, rm in enumerate(rms):
        row = table.rows[idx]

        # ----------------------------------------
        # Separator (PARITY with rich)
        # ----------------------------------------
        if idx < len(row_keys) and row_keys[idx] is None:
            label = _normalize(_get_sep_label(rm))

            n_cols = len(table.columns) + (1 if explain else 0)

            # blank spacer row
            html.append(f"<tr><td colspan='{n_cols}'>&nbsp;</td></tr>")

            # section header row
            html.append(
                f"<tr><td colspan='{n_cols}' "
                f"style='font-weight:bold; text-align:left; padding-top:8px;'>"
                f"{escape(label)}</td></tr>"
            )
            continue

        # ----------------------------------------
        # Metric row
        # ----------------------------------------
        label = _normalize(row[0])
        html.append("<tr>")

        html.append(f"<td style='text-align:left'>{escape(label)}</td>")

        row_key = row_keys[idx] if idx < len(row_keys) else None
        wrap_width = row_wrap.get(row_key)

        # Values
        for i in range(1, len(row)):
            col_key = column_keys[i]
            align = align_map.get(col_key, "right")

            val = _extract(row[i])
            val = "" if val is None else str(val)

            if wrap_width:
                val = fill(val, width=wrap_width)

            style = _style_align(align)
            html.append(f"<td style='{style}'>{escape(val)}</td>")

        # Explanation
        if explain:
            explanation = explain_metric_series(rm, rows_data, explain)
            html.append(f"<td style='text-align:left'>{escape(explanation)}</td>")

        html.append("</tr>")

    html.append("</tbody></table>")

    return "\n".join(html)


# =========================================================
# MAIN ENTRY
# =========================================================
def render_html_table(table):
    """
    Drop-in HTML renderer with FULL parity to rich_table.

    Supports:
        - layout = "table"
        - layout = "pivot"
    """

    if not table or not table.columns:
        return "<div class='roost-empty'>No data</div>"

    if table.layout == "pivot":
        return _render_pivot(table)
    else:
        return _render_table(table)
