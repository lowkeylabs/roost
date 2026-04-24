# src/owlroost/domain/services/renderers/markdown_table.py


# =========================================================
# Helpers
# =========================================================
def _extract(cell):
    if isinstance(cell, dict):
        return cell.get("formatted")
    return cell


def _normalize(label):
    return str(label).replace("\n", " ").strip()


def _get_sep_label(rm):
    if isinstance(rm, dict):
        return rm.get("separator_label", "") or ""
    return getattr(rm, "separator_label", "") or ""


# =========================================================
# Pivot renderer (Markdown)
# =========================================================
def _render_pivot_markdown(table, separate_tables=True):
    from owlroost.domain.metrics.metric_spec import explain_metric_series

    row_keys = table.meta.get("row_keys", [])
    rms = table.meta.get("rms", [])
    rows_data = table.meta.get("rows", [])
    explain = table.meta.get("explain") or set()

    # ----------------------------------------
    # Header builder
    # ----------------------------------------
    headers = [_normalize(table.columns[0])] + [_normalize(c) for c in table.columns[1:]]
    if explain:
        headers.append("Explanation")

    n_cols = len(headers)

    def start_table():
        return [
            "",
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * n_cols) + " |",
        ]

    lines = []
    in_table = False

    for idx, rm in enumerate(rms):
        row = table.rows[idx]

        # ----------------------------------------
        # SECTION BREAK
        # ----------------------------------------
        if idx < len(row_keys) and row_keys[idx] is None:
            label = _normalize(_get_sep_label(rm))

            if separate_tables:
                if in_table:
                    lines.append("")
                    in_table = False

                if label:
                    lines.append("")
                    lines.append(f"## {label}")
                    lines.append("")
            else:
                if not in_table:
                    lines.extend(start_table())
                    in_table = True

                if label:
                    # CLEAN, VALID SINGLE ROW (no tricks)
                    row_cells = [f"**{label}**"] + [""] * (n_cols - 1)
                    lines.append("| " + " | ".join(row_cells) + " |")

            continue

        # ----------------------------------------
        # START TABLE IF NEEDED
        # ----------------------------------------
        if not in_table:
            lines.extend(start_table())
            in_table = True

        # ----------------------------------------
        # NORMAL ROW
        # ----------------------------------------
        # 🔥 STRONG normalize (guaranteed no newlines)
        label = " ".join(str(row[0]).split())

        values = []
        for i in range(1, len(row)):
            val = _extract(row[i])
            val = "" if val is None else str(val)

            # 🔥 convert multiline → safe HTML
            val = val.replace("\n", "<br>")

            values.append(val)

        # 🔥 FIX: explanation MUST also be normalized
        if explain:
            explanation = explain_metric_series(rm, rows_data, explain)
            explanation = "" if explanation is None else str(explanation)
            explanation = explanation.replace("\n", "<br>")
            values.append(explanation)

        # enforce rectangular table
        row_cells = [label] + values
        row_cells += [""] * (n_cols - len(row_cells))

        lines.append("| " + " | ".join(row_cells) + " |")

    lines.append("")
    return "\n".join(lines)


# =========================================================
# Table renderer (row-wise fallback)
# =========================================================
def _render_table_markdown(table):
    visible_cols = [i for i, col in enumerate(table.columns) if col != "run_label"]

    headers = [str(table.columns[i]) for i in visible_cols]
    n_cols = len(headers)

    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * n_cols) + " |")

    for row in table.rows:
        vals = []
        for i in visible_cols:
            val = _extract(row[i])
            val = "" if val is None else str(val)
            vals.append(val)

        vals += [""] * (n_cols - len(vals))
        lines.append("| " + " | ".join(vals) + " |")

    lines.append("")
    return "\n".join(lines)


# =========================================================
# Public API
# =========================================================
def render_markdown_table(table, separate_tables=True):
    if not table or not table.columns:
        return "_No data_"

    if table.layout == "pivot":
        return _render_pivot_markdown(table, separate_tables=separate_tables)
    else:
        return _render_table_markdown(table)
