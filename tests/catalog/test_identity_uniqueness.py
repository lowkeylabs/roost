from __future__ import annotations


def test_catalog_field_names_unique(
    catalog_dataset,
):
    names = [row["field_name"] for row in catalog_dataset.rows]

    assert len(names) == len(set(names))
