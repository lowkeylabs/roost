from __future__ import annotations


def test_namespace_nodes_not_materialized(
    catalog_rows,
):
    """
    Namespace hierarchy should not be
    materialized as canonical semantic
    variables.
    """

    namespace_names = {
        "timing",
        "risk",
        "financial",
        "display",
        "run_execution",
    }

    names = {row["field_name"] for row in catalog_rows}

    for namespace in namespace_names:
        assert namespace not in names
