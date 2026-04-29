# src/owlroost/domain/reporting/report_tools.py

from owlroost.domain.metrics.view_registry import get_view
from owlroost.domain.services.renderers.html_table import render_html_table
from owlroost.domain.services.renderers.latex_table import render_latex_table
from owlroost.domain.services.view_materializer import materialize_view


def render_relevant_table(table):
    ss = f"""
::: {{.content-visible when-format="html"}}
{render_html_table(table)}
:::
::: {{.content-visible when-format="pdf"}}
{render_latex_table(table)}
:::
"""
    return ss


def generate_table(bundle, level="run", view="default", layout="table", explain=None):
    # ----------------------------------------
    # Normalize + validate inputs
    # ----------------------------------------
    level = level.lower()
    if level not in ("run", "trial"):
        raise ValueError(f"Invalid level '{level}' (expected 'run' or 'trial')")

    explain = set(explain or [])

    # ----------------------------------------
    # Select rows
    # ----------------------------------------
    key = "trial_rows" if level == "trial" else "run_rows"

    if key not in bundle:
        raise KeyError(f"Bundle missing '{key}'")

    rows = bundle[key]

    # ----------------------------------------
    # Resolve view
    # ----------------------------------------
    selected_view, _, view_explain = get_view(level, view)

    # Merge explain (user overrides default)
    if not explain and view_explain:
        explain = set(view_explain)

    # ----------------------------------------
    # Materialize table
    # ----------------------------------------
    return materialize_view(
        rows,
        selected_view,
        layout=layout,
        explain=explain,
    )
