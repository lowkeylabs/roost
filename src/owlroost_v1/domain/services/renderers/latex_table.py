# src/owlroost/domain/services/renderers/latex_table.py

# =========================================================
# Helpers
# =========================================================
def _extract(cell):
    if isinstance(cell, dict):
        return cell.get("formatted")
    return cell


def _latex_escape(s):
    if s is None:
        return ""
    s = str(s)

    # Preserve line breaks for LaTeX
    s = s.replace("\n", r"\newline ")

    return (
        s.replace("&", r"\&")
        .replace("%", r"\%")
        .replace("$", r"\$")
        .replace("#", r"\#")
        .replace("_", r"\_")
        .replace("{", r"\{")
        .replace("}", r"\}")
    )


def _normalize(label):
    return str(label).replace("\n", " ").strip()


def _get_sep_label(rm):
    if isinstance(rm, dict):
        return rm.get("separator_label", "") or ""
    return getattr(rm, "separator_label", "") or ""


# =========================================================
# Column spec builder (IMPROVED)
# =========================================================
def _build_column_spec(table, explain):
    align_map = table.meta.get("align", {})
    column_keys = table.meta.get("column_keys", table.columns)

    n_data_cols = len(table.columns) - 1 + (1 if explain else 0)

    # ----------------------------------------
    # GLOBAL SCALE (THIS is the fix)
    # ----------------------------------------
    scale = 0.75  # ← change this to control table width

    # ----------------------------------------
    # Allocate widths proportionally
    # ----------------------------------------
    metric_ratio = 0.35
    metric_width = metric_ratio * scale

    remaining = scale - metric_width
    per_col = remaining / max(n_data_cols, 1)

    specs = []

    # Metric column (wider)
    specs.append(f"p{{{metric_width:.3f}\\textwidth}}")

    for i in range(1, len(table.columns)):
        col_key = column_keys[i]
        align = align_map.get(col_key, "right")

        if align == "left":
            specs.append(f"p{{{per_col:.3f}\\textwidth}}")
        elif align == "center":
            specs.append(f">{{\\centering\\arraybackslash}}p{{{per_col:.3f}\\textwidth}}")
        else:
            specs.append(f">{{\\raggedleft\\arraybackslash}}p{{{per_col:.3f}\\textwidth}}")

    if explain:
        specs.append(f"p{{{per_col:.3f}\\textwidth}}")

    return "".join(specs)


# =========================================================
# Pivot renderer (JOURNAL STYLE)
# =========================================================
def _render_pivot_latex(table):
    row_keys = table.meta.get("row_keys", [])
    explain = table.meta.get("explain") or set()
    rms = table.meta.get("rms", [])
    rows_data = table.meta.get("rows", [])

    from owlroost.domain.metrics.metric_spec import explain_metric_series

    lines = []

    col_spec = _build_column_spec(table, explain)

    # ----------------------------------------
    # Begin table (FIXED STRUCTURE)
    # ----------------------------------------
    # ----------------------------------------
    # Begin table (FIXED: no adjustbox, no center)
    # ----------------------------------------
    lines.append(r"\begingroup")
    lines.append(r"\setlength{\tabcolsep}{8pt}")
    lines.append(r"\renewcommand{\arraystretch}{1.2}")

    lines.append(r"\begin{longtable}{" + col_spec + "}")
    lines.append(r"\caption{Retirement Plan Metrics}\\")
    lines.append(r"\toprule")

    # ----------------------------------------
    # Header
    # ----------------------------------------
    headers = [_normalize(table.columns[0])]
    headers += [_normalize(c) for c in table.columns[1:]]

    if explain:
        headers.append("Explanation")

    header_line = " & ".join(r"\textbf{" + _latex_escape(h) + "}" for h in headers) + r" \\"

    lines.append(header_line)
    lines.append(r"\midrule")
    lines.append(r"\endfirsthead")

    # repeat header on new pages
    lines.append(r"\toprule")
    lines.append(header_line)
    lines.append(r"\midrule")
    lines.append(r"\endhead")

    # ----------------------------------------
    # Rows
    # ----------------------------------------
    for idx, rm in enumerate(rms):
        row = table.rows[idx]

        # ----------------------------------------
        # Section header (clean + spaced)
        # ----------------------------------------
        if row_keys[idx] is None:
            label = _normalize(_get_sep_label(rm))

            if label:
                lines.append(r"\addlinespace[0.75em]")
                lines.append(
                    r"\multicolumn{"
                    + str(len(headers))
                    + r"}{l}{\textbf{\large "
                    + _latex_escape(label)
                    + r"}} \\"
                )
                lines.append(r"\addlinespace[0.25em]")
            continue

        # ----------------------------------------
        # Normal row
        # ----------------------------------------
        # label = r"\textbf{" + _latex_escape(_normalize(row[0])) + "}"
        label = _latex_escape(_normalize(row[0]))

        values = []
        for i in range(1, len(row)):
            val = _extract(row[i])
            val = "" if val is None else _latex_escape(val)
            values.append(val)

        if explain:
            explanation = explain_metric_series(rm, rows_data, explain)
            explanation = "" if explanation is None else _latex_escape(explanation)
            values.append(explanation)

        lines.append(" & ".join([label] + values) + r" \\")

    # ----------------------------------------
    # End table
    # ----------------------------------------
    lines.append(r"\bottomrule")
    lines.append(r"\end{longtable}")
    lines.append(r"\endgroup")

    return "\n".join(lines)


# =========================================================
# Simple table renderer
# =========================================================
def _render_table_latex(table):
    headers = [_normalize(c) for c in table.columns]

    lines = []
    lines.append(r"\begin{tabular}{" + "l" * len(headers) + "}")
    lines.append(r"\toprule")

    lines.append(" & ".join(_latex_escape(h) for h in headers) + r" \\")
    lines.append(r"\midrule")

    for row in table.rows:
        vals = [_latex_escape(_extract(c)) for c in row]
        lines.append(" & ".join(vals) + r" \\")

    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")

    return "\n".join(lines)


# =========================================================
# Public API
# =========================================================
def render_latex_table(table):
    if not table or not table.columns:
        return r"\textit{No data}"

    if table.layout == "pivot":
        return _render_pivot_latex(table)
    else:
        return _render_table_latex(table)
