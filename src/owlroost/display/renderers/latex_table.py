# src/owlroost/display/renderers/latex_table.py


def render_latex_table(table):
    cols = table.columns
    rows = table.rows

    header = " & ".join(cols) + " \\\\ \\hline"
    body = [" & ".join(str(c) for c in r) + " \\\\" for r in rows]

    return "\n".join(
        [
            "\\begin{tabular}{" + "l" * len(cols) + "}",
            "\\hline",
            header,
            *body,
            "\\hline",
            "\\end{tabular}",
        ]
    )
