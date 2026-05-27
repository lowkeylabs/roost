# tests/integration/test_architecture_pipeline.py

from __future__ import annotations

from owlroost.catalog.loaders import (
    load_catalog_dataset,
)

from owlroost.display.bootstrap import (
    build_display_registry,
)

from owlroost.display.renderers.rich_table import (
    render_rich_table,
)

from owlroost.metrics.bootstrap import (
    build_metrics_registry,
)

from owlroost.schema.bootstrap import (
    build_registry,
)


def test_architecture_pipeline():
    """
    High-level ROOST architecture integration test.

    This test intentionally validates the
    end-to-end semantic pipeline used by
    renderer-facing workflows.

    Architectural layers validated:

        schema
            ↓
        metrics
            ↓
        display overlays
            ↓
        catalog synthesis
            ↓
        dataset materialization
            ↓
        view projection
            ↓
        renderer-facing tables
            ↓
        rendering pipeline

    This test intentionally validates
    subsystem contracts and ontology
    invariants rather than narrow
    implementation details.
    """

    # =====================================================
    # Schema Registry
    # =====================================================

    schema_registry = build_registry()

    assert schema_registry is not None

    assert len(schema_registry) > 0

    # =====================================================
    # Metrics Registry
    # =====================================================

    metrics_registry = (
        build_metrics_registry()
    )

    assert metrics_registry is not None

    assert len(metrics_registry) > 0

    # =====================================================
    # Display Registry
    # =====================================================

    display_registry = (
        build_display_registry(
            schema_registry=(
                schema_registry
            ),
            metrics_registry=(
                metrics_registry
            ),
        )
    )

    assert display_registry is not None

    # -----------------------------------------------------
    # Display overlays should exist
    # -----------------------------------------------------

    assert (
        len(display_registry.all())
        > 0
    )

    # =====================================================
    # Catalog Dataset
    # =====================================================

    ds = load_catalog_dataset(
        schema_registry=(
            schema_registry
        ),
        metrics_registry=(
            metrics_registry
        ),
        display_registry=(
            display_registry
        ),
    )

    assert ds is not None

    # -----------------------------------------------------
    # Dataset identity
    # -----------------------------------------------------

    assert ds.level == "catalog"

    # -----------------------------------------------------
    # Catalog rows should exist
    # -----------------------------------------------------

    assert ds.rows

    # =====================================================
    # Catalog View Materialization
    # =====================================================

    table = ds.view(
        registry=display_registry,
        name="catalog",
        layout="table",
    )

    # -----------------------------------------------------
    # Renderer-facing table should exist
    # -----------------------------------------------------

    assert table is not None

    # -----------------------------------------------------
    # Table should contain columns
    # -----------------------------------------------------

    assert table.columns

    # -----------------------------------------------------
    # Table should contain rows
    # -----------------------------------------------------

    assert table.rows

    # =====================================================
    # Renderer Pipeline
    # =====================================================

    rendered = render_rich_table(
        table,
    )

    assert rendered is not None

    # =====================================================
    # Ontology Invariants
    # =====================================================

    field_names: set[str] = set()

    for row in ds.rows:

        # -------------------------------------------------
        # Canonical semantic identity required
        # -------------------------------------------------

        assert row["field_name"]

        # -------------------------------------------------
        # Semantic identities must be unique
        # -------------------------------------------------

        assert (
            row["field_name"]
            not in field_names
        )

        field_names.add(
            row["field_name"]
        )

        # -------------------------------------------------
        # Ontology ownership required
        # -------------------------------------------------

        assert row.get("owner")

        # -------------------------------------------------
        # Projection semantics required
        # -------------------------------------------------

        assert row.get(
            "projection_kind"
        )

        # -------------------------------------------------
        # Runtime materialization required
        # -------------------------------------------------

        assert row.get(
            "materialization_level"
        )

        # -------------------------------------------------
        # Namespace-only rows should not appear
        # -------------------------------------------------

        assert not row[
            "field_name"
        ].endswith(".")

    # =====================================================
    # Aggregate Projection Invariants
    # =====================================================

    aggregate_rows = [
        r
        for r in ds.rows
        if (
            r.get("projection_kind")
            == "aggregate"
        )
    ]

    for row in aggregate_rows:

        # -------------------------------------------------
        # Aggregate field naming convention
        # -------------------------------------------------

        assert "__" in row[
            "field_name"
        ]

        # -------------------------------------------------
        # Aggregate lineage required
        # -------------------------------------------------

        assert row.get(
            "derived_from"
        )

    # =====================================================
    # Display Overlay Invariants
    # =====================================================

    overlay_names = set()

    for field in display_registry.all():

        assert field.field_name

        overlay_names.add(
            field.field_name
        )

    # -----------------------------------------------------
    # Display overlays should align to
    # semantic catalog identities.
    # -----------------------------------------------------

    assert (
        field_names
        & overlay_names
    )
    