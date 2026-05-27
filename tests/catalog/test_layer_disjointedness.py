from __future__ import annotations


def test_schema_metrics_disjoint(
    catalog_dataset,
):

    schema_names = {
        row["field_name"]
        for row in catalog_dataset.rows
        if row["layer"] == "schema"
    }

    metric_names = {
        row["field_name"]
        for row in catalog_dataset.rows
        if row["layer"] == "metrics"
    }

    assert (
        schema_names
        & metric_names
        == set()
    )
