# tests/integration/test_architecture_pipeline.py

from __future__ import annotations

from owlroost.catalog.ontology import (
    CatalogNodeType,
)
from owlroost.catalog.service import (
    load_catalog,
)
from owlroost.display.bootstrap import (
    build_display_registry,
)
from owlroost.display.materializers.materialize import (
    materialize_view,
)
from owlroost.display.renderers.rich_table import (
    render_rich_table,
)
from owlroost.metrics.bootstrap import (
    build_metrics_registry,
)
from owlroost.schema.bootstrap import (
    build_schema_registry,
)

# =========================================================
# Semantic Node Types
# =========================================================

SEMANTIC_NODE_TYPES = {
    CatalogNodeType.VARIABLE,
}


# =========================================================
# Architecture Pipeline
# =========================================================


def test_architecture_pipeline():
    """
    End-to-end architecture validation.

    Current Architecture
    --------------------

    Schema Registry
        owns semantic variables

    Metrics Registry
        owns semantic variables

    Display Registry
        owns presentation overlays and
        may declare synthetic semantic
        variables

    Catalog
        owns canonical semantic identity

    Materializer
        consumes catalog semantics and
        display presentation overlays

    Renderer
        consumes materialized tables

    Notes
    -----
    Namespace catalog nodes no longer
    exist.

    Hierarchy is represented through:

        - field_name
        - path

    rather than synthetic namespace
    entities.
    """

    # =====================================================
    # Schema
    # =====================================================

    schema_registry = build_schema_registry()

    assert schema_registry

    schema_field_names = {field.name for field in schema_registry.all()}

    # =====================================================
    # Schema owns semantic leaves only
    # =====================================================

    assert "aca_settings" not in schema_field_names

    assert "solver_options" not in schema_field_names

    assert "optimization_parameters" not in schema_field_names

    assert "aca_settings.slcsp_annual" in schema_field_names

    assert "solver_options.bequest" in schema_field_names

    # =====================================================
    # Metrics
    # =====================================================

    metrics_registry = build_metrics_registry()

    assert metrics_registry

    # =====================================================
    # Display
    # =====================================================

    display_registry = build_display_registry(
        schema_registry=schema_registry,
        metrics_registry=metrics_registry,
    )

    assert display_registry

    assert len(display_registry.all_field_names()) > 0

    # =====================================================
    # Fixture Architecture
    # =====================================================

    assert display_registry.has_view(
        "case",
        "testing-fixture",
    )

    assert display_registry.has_group(
        "testing.expansion",
    )

    assert display_registry.has_display_field(
        "testing.scalar",
    )

    # =====================================================
    # Catalog
    # =====================================================

    catalog_rows = load_catalog(
        schema_registry=schema_registry,
        metrics_registry=metrics_registry,
        display_registry=display_registry,
    )

    assert catalog_rows

    catalog_field_names = {row["field_name"] for row in catalog_rows}

    # =====================================================
    # Materialization
    # =====================================================

    table = materialize_view(
        rows=catalog_rows,
        registry=display_registry,
        level="case",
        view_name="testing-fixture",
    )

    assert table is not None

    assert table.columns

    assert table.rows

    # =====================================================
    # Rendering
    # =====================================================

    rendered = render_rich_table(
        table,
    )

    assert rendered is not None

    # =====================================================
    # Catalog Identity Invariants
    # =====================================================

    field_names: set[str] = set()

    semantic_rows = []

    overlay_rows = []

    for row in catalog_rows:
        field_name = row["field_name"]

        assert field_name

        assert field_name not in field_names

        field_names.add(
            field_name,
        )

        assert not field_name.endswith(".")

        node_type = row.get(
            "node_type",
        )

        assert node_type is not None, f"{field_name}: missing node_type"

        # -------------------------------------------------
        # Semantic Variables
        # -------------------------------------------------

        if node_type in SEMANTIC_NODE_TYPES:
            semantic_rows.append(
                row,
            )

            assert row.get("owner"), f"{field_name}: missing owner"

            assert row.get("projection_kind"), f"{field_name}: missing projection_kind"

            assert row.get("materialization_level"), f"{field_name}: missing materialization_level"

        # -------------------------------------------------
        # Overlay Variables
        # -------------------------------------------------

        elif node_type == CatalogNodeType.OVERLAY:
            overlay_rows.append(
                row,
            )

        # -------------------------------------------------
        # Unknown Node Type
        # -------------------------------------------------

        else:
            raise AssertionError(f"{field_name}: unknown node_type '{node_type}'")

    assert semantic_rows

    # =====================================================
    # Catalog ↔ Schema Relationship
    # =====================================================

    missing_schema_fields = schema_field_names - catalog_field_names

    assert not missing_schema_fields, (
        f"Schema fields missing from catalog: {sorted(missing_schema_fields)}"
    )

    # =====================================================
    # Catalog ↔ Metrics Relationship
    # =====================================================

    metric_rows = [row for row in catalog_rows if row.get("layer") == "metrics"]

    assert metric_rows

    aggregate_rows = [row for row in metric_rows if "__" in row["field_name"]]

    assert aggregate_rows

    # =====================================================
    # Aggregate Invariants
    # =====================================================

    aggregate_rows = [row for row in catalog_rows if (row.get("projection_kind") == "aggregate")]

    aggregate_names = {row["field_name"] for row in aggregate_rows}

    for row in aggregate_rows:
        assert "__" in row["field_name"]

        assert row.get("derived_from")

    expected_aggregates = {
        "timing.elapsed_seconds__mean",
        "timing.elapsed_seconds__median",
        "timing.elapsed_seconds__p90",
    }

    assert expected_aggregates <= aggregate_names

    # =====================================================
    # Display Registry Participation
    # =====================================================

    display_names = set(display_registry.all_field_names())

    assert display_names & catalog_field_names

    # =====================================================
    # Testing Display Fixtures
    # =====================================================

    expected_fixture_fields = {
        "testing.scalar",
        "testing.string",
        "testing.boolean",
        "testing.composed",
        "testing.semantic",
    }

    missing = expected_fixture_fields - catalog_field_names

    assert not missing, f"Testing display fixtures must participate in catalog: {sorted(missing)}"

    # =====================================================
    # Explicit Semantic Fixture
    # =====================================================

    assert "testing.semantic" in catalog_field_names

    semantic_fixture = next(
        row for row in catalog_rows if (row["field_name"] == "testing.semantic")
    )

    assert semantic_fixture["owner"] == "ROOST"

    assert semantic_fixture["semantic_domain"] == "execution"

    assert semantic_fixture["value_origin"] == "roost-computed"

    assert semantic_fixture["projection_kind"] == "synthetic"

    # =====================================================
    # Catalog Sources
    # =====================================================

    layer_values = {row.get("layer") for row in catalog_rows}

    assert "schema" in layer_values
    assert "metrics" in layer_values
    assert "display" in layer_values
