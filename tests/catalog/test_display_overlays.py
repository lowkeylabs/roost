from __future__ import annotations


def test_display_does_not_duplicate_semantic_rows(
    catalog_dataset,
):

    counts = {}

    for row in catalog_dataset.rows:

        name = row["field_name"]

        counts[name] = (
            counts.get(name, 0)
            + 1
        )

    duplicates = {
        k: v
        for k, v in counts.items()
        if v > 1
    }

    assert duplicates == {}
