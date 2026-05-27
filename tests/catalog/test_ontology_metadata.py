from __future__ import annotations


def test_catalog_rows_have_owner(
    catalog_dataset,
):

    rows = [
        row
        for row in catalog_dataset.rows
        if row["owner"] is not None
    ]

    assert rows


def test_catalog_rows_have_projection_kind(
    catalog_dataset,
):

    for row in catalog_dataset.rows:

        assert (
            row["projection_kind"]
            is not None
        )


def test_catalog_rows_have_materialization_level(
    catalog_dataset,
):

    for row in catalog_dataset.rows:

        assert (
            row["materialization_level"]
            is not None
        )
