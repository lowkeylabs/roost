from __future__ import annotations


def test_aggregate_metrics_have_aggregate_projection(
    catalog_rows,
):
    rows = [row for row in catalog_rows if "__" in row["field_name"]]

    assert rows

    for row in rows:
        assert row["projection_kind"] == "aggregate"
