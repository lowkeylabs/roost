# src/owlroost/domain/services/render_table.py

from owlroost.domain.services.renderers.rich_table import render_rich_table
from owlroost.domain.services.view_materializer import materialize_view


# =========================================================
# Engine dispatcher
# =========================================================
def render_with_engine(console, table, engine="rich"):
    if engine == "rich":
        return render_rich_table(console, table)

    elif engine == "pandas":
        console.print(table.to_dataframe())

    elif engine == "none":
        return table

    else:
        raise ValueError(f"Unknown engine: {engine}")


# =========================================================
# Main dispatcher (THIN WRAPPER)
# =========================================================
def render_table(
    console,
    rows,
    view,
    layout="table",
    explain: set[str] | None = None,
    engine="rich",
):
    table = materialize_view(
        rows,
        view,
        layout=layout,
        explain=explain,
    )

    return render_with_engine(console, table, engine=engine)
