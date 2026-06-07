from __future__ import annotations


def test_schema_metrics_disjoint(
    catalog_rows: list[dict[str, str | None]],
):
    schema_names = {row["field_name"] for row in catalog_rows if row["layer"] == "schema"}

    metric_names = {row["field_name"] for row in catalog_rows if row["layer"] == "metrics"}

    assert schema_names & metric_names == set()
