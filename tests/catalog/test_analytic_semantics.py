# tests/catalog/test_analytic_semantics.py

from __future__ import annotations

# =========================================================
# Ontology Completeness
# =========================================================


def test_catalog_rows_have_analytic_kind(
    catalog_rows,
):
    """
    Ensure at least some catalog rows
    explicitly define analytical semantics.
    """

    rows = [row for row in catalog_rows if row["analytic_kind"] is not None]

    assert rows


# =========================================================
# Comparative Semantics
# =========================================================


def test_comparative_metrics_have_comparative_analytic_kind(
    catalog_rows,
):
    """
    Comparative analytical metrics should
    explicitly advertise comparative
    semantics.
    """

    comparative_rows = [
        row
        for row in catalog_rows
        if row["field_name"]
        in {
            ("run_execution.common_overrides"),
            ("run_execution.run_specific_overrides"),
        }
    ]

    assert comparative_rows

    for row in comparative_rows:
        assert row["analytic_kind"] == "comparative"


# =========================================================
# Aggregate Projection Integrity
# =========================================================


def test_aggregate_projection_rows_have_aggregate_semantics(
    catalog_rows,
):
    """
    Aggregate projections should advertise
    aggregate analytical semantics.
    """

    aggregate_rows = [row for row in catalog_rows if row["projection_kind"] == "aggregate"]

    for row in aggregate_rows:
        assert row["analytic_kind"] in {
            "aggregate",
            "distributional",
        }


# =========================================================
# Canonical Schema Semantics
# =========================================================


def test_schema_rows_are_canonical(
    catalog_rows,
):
    """
    Schema ontology should represent
    canonical semantic variables.
    """

    schema_rows = [row for row in catalog_rows if row["layer"] == "schema"]

    assert schema_rows

    for row in schema_rows:
        assert row["projection_kind"] == "canonical"


# =========================================================
# Namespace Separation
# =========================================================


def test_only_semantic_variables_materialized(
    catalog_rows,
):
    """
    Canonical catalog synthesis should
    currently materialize only semantic
    variable nodes.
    """

    for row in catalog_rows:
        assert row["node_type"] == "variable"


# =========================================================
# Overlay Projection Integrity
# =========================================================


def test_all_rows_have_analytic_kind(
    catalog_rows,
):
    """
    Every semantic variable should declare
    analytical semantics.
    """

    for row in catalog_rows:
        assert row["analytic_kind"] is not None
