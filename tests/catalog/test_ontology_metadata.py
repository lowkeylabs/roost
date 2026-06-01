from __future__ import annotations


def test_catalog_rows_have_owner(
    catalog_rows,
):
    rows = [row for row in catalog_rows if row["owner"] is not None]

    assert rows


def test_catalog_rows_have_projection_kind(
    catalog_rows,
):
    for row in catalog_rows:
        assert row["projection_kind"] is not None


def test_catalog_rows_have_materialization_level(
    catalog_rows,
):
    for row in catalog_rows:
        assert row["materialization_level"] is not None
