# tests/integration/test_architecture_pipeline.py

from __future__ import annotations

from owlroost.catalog.loaders import (
    load_catalog,
)
from owlroost.catalog.ontology import (
    CatalogNodeType,
    ProjectionKind,
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

    Model B2
    --------
    Schema Registry
        owns semantic variables only

    Catalog
        owns graph structure

    Display
        owns presentation overlays

    Materializer
        consumes catalog rows

    Renderer
        consumes materialized tables
    """

    # =====================================================
    # Schema
    # =====================================================

    schema_registry = build_schema_registry()

    assert schema_registry

    schema_field_names = {field.name for field in schema_registry.all()}

    # =====================================================
    # Model B2:
    # schema owns leaves only
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
    )

    assert catalog_rows

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

    namespace_rows = []

    overlay_rows = []

    for row in catalog_rows:
        field_name = row["field_name"]

        assert field_name

        assert field_name not in field_names

        field_names.add(
            field_name,
        )

        assert not field_name.endswith(".")

        node_type = row.get("node_type")

        assert node_type is not None, f"{field_name}: missing node_type"

        # -------------------------------------------------
        # Semantic Nodes
        # -------------------------------------------------

        if node_type in SEMANTIC_NODE_TYPES:
            semantic_rows.append(
                row,
            )

            assert row.get("owner"), f"{field_name}: semantic node missing owner"

            assert row.get("projection_kind"), (
                f"{field_name}: semantic node missing projection_kind"
            )

            assert row.get("materialization_level"), (
                f"{field_name}: semantic node missing materialization_level"
            )

            if "." not in field_name:
                assert field_name in {
                    "case_name",
                    "description",
                }, f"{field_name}: top-level semantic node looks like container"

        # -------------------------------------------------
        # Namespace Nodes
        # -------------------------------------------------

        elif node_type == CatalogNodeType.NAMESPACE:
            namespace_rows.append(
                row,
            )

            assert row.get("owner") is None

            assert row.get("semantic_domain") is None

            assert row.get("value_origin") is None

        # -------------------------------------------------
        # Overlay Nodes
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

    assert namespace_rows

    # =====================================================
    # Namespace Hierarchy Invariants
    # =====================================================

    catalog_field_names = {row["field_name"] for row in catalog_rows}

    expected_namespaces = {
        "aca_settings",
        "solver_options",
        "optimization_parameters",
    }

    actual_namespaces = {row["field_name"] for row in namespace_rows}

    assert expected_namespaces <= actual_namespaces

    for row in namespace_rows:
        namespace = row["field_name"]

        # ---------------------------------------------
        # Model B2:
        # namespace nodes belong to catalog,
        # not schema.
        # ---------------------------------------------

        assert namespace not in schema_field_names, (
            f"{namespace}: namespace node should not exist in schema registry"
        )

        prefix = namespace + "."

        descendants = [
            candidate for candidate in catalog_field_names if candidate.startswith(prefix)
        ]

        assert descendants, f"{namespace}: namespace node has no descendants"

    # =====================================================
    # Aggregate Invariants
    # =====================================================

    aggregate_rows = [
        row for row in catalog_rows if (row.get("projection_kind") == ProjectionKind.AGGREGATE)
    ]

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
    # Display Overlay Invariants
    # =====================================================

    overlay_names = set(display_registry.all_field_names())

    assert field_names & overlay_names

    # =====================================================
    # Display ↔ Catalog Linkage
    # =====================================================

    for field_name in display_registry.all_field_names():
        field = display_registry.get_display_field(
            field_name,
        )

        ontology_field = getattr(
            field,
            "ontology_field",
            None,
        )

        if ontology_field is None:
            continue

        assert field.field_name in catalog_field_names

    # =====================================================
    # Synthetic Variables
    # =====================================================

    synthetic_rows = [
        row for row in catalog_rows if (row.get("projection_kind") == ProjectionKind.SYNTHETIC)
    ]

    synthetic_names = {row["field_name"] for row in synthetic_rows}

    expected_synthetic_fields = {
        "display.net_worth",
        "display.total_assets",
        "display.fixed_income",
        "display.current_ages",
        "display.life_expectancy",
    }

    missing = expected_synthetic_fields - synthetic_names

    assert not missing, (
        f"Synthetic display variables must participate in catalog: {sorted(missing)}"
    )
