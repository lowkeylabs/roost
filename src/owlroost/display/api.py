# src/owlroost/display/api.py

from .renderers.latex_table import render_latex_table
from .renderers.markdown_table import render_markdown_table
from .renderers.rich_table import render_rich_table
from .table import Table
from .utils import extract_path
from .views import VIEWS


# ---------------------------------------------------------
# View extraction (minimal, no registry yet)
# ---------------------------------------------------------
def extract_view(dataset, view="default", layout="table"):
    if view not in VIEWS:
        raise ValueError(f"Unknown view: {view}")

    fields = VIEWS[view]

    columns = fields
    rows = []

    for row in dataset.rows:
        out = []

        for f in fields:
            value = extract_path(row, f)
            out.append("" if value is None else str(value))

        rows.append(out)

    return Table(columns, rows)


# ---------------------------------------------------------
# Rendering
# ---------------------------------------------------------
def render(table, renderer="rich"):
    if renderer == "rich":
        return render_rich_table(table)

    if renderer == "markdown":
        return render_markdown_table(table)

    if renderer == "latex":
        return render_latex_table(table)

    raise ValueError(f"Unknown renderer: {renderer}")
