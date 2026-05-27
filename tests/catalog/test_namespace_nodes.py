from __future__ import annotations

import pytest


@pytest.mark.xfail(
    reason=(
        "Namespace nodes not yet "
        "fully separated from "
        "semantic variables."
    )
)
def test_namespace_nodes_not_materialized(
    catalog_dataset,
):

    names = {
        row["field_name"]
        for row in catalog_dataset.rows
    }

    assert "timing" not in names
