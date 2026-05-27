from __future__ import annotations

from owlroost.display.renderers.specs import (
    TableColumn,
)


# =========================================================
# Table Utilities
# =========================================================


def inject_id_column(
    table,
    dataset,
):
    """
    Inject dataset row IDs into table.
    """

    table.columns = [
        TableColumn(
            key="_row_id",
            label="ID",
            label_align="right",
            content_align="right",
        )
    ] + list(table.columns)

    new_rows = []

    for row_data, r in zip(
        table.rows,
        dataset.rows,
        strict=False,
    ):
        new_rows.append(
            [str(r["_row_id"])] + list(row_data)
        )

    table.rows = new_rows

    return table
