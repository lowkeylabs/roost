# src/owlroost/display/views/views.py

from __future__ import annotations

from owlroost.display.specs import (
    DisplayView,
)


def register_display_views(
    reg,
):
    """
    Register all display views.

    Views are declarative layouts composed
    from reusable display groups and fields.

    Views are uniquely identified by:

        (level, name)

    Examples:

        ("case", "basic")
        ("run", "results")
        ("session", "results")
    """

    # =====================================================
    # CASE VIEWS
    # =====================================================

    reg.register_view(
        DisplayView(
            level="case",
            name="cases",
            entries=[
                ("case_name"),
                ("group", "top_level"),
                # ("group", "planning"),
            ],
            description=(
                "Default case dashboard showing "
                "household demographics, high-level "
                "financial structure, and planning "
                "configuration."
            ),
        )
    )

    reg.register_view(
        DisplayView(
            level="case",
            name="build",
            entries=[
                ("group", "identity"),
                # ("group", "balances"),
                ("group", "planning"),
            ],
            description=(
                "Default case dashboard showing "
                "household demographics, high-level "
                "financial structure, and planning "
                "configuration."
            ),
        )
    )

    reg.register_view(
        DisplayView(
            level="case",
            name="results",
            entries=[
                ("group", "identity"),
                ("group", "inventory"),
            ],
            description=(
                "Operational case summary showing "
                "execution provenance and aggregate "
                "run/trial inventory."
            ),
        )
    )

    reg.register_view(
        DisplayView(
            level="case",
            name="balances",
            entries=[
                ("group", "identity"),
                ("group", "balances"),
            ],
            description=(
                "Household balance sheet summary "
                "including retirement savings structure, "
                "fixed assets, debts, net worth, "
                "and guaranteed retirement income."
            ),
        )
    )

    # =====================================================
    # SESSION VIEWS
    # =====================================================

    reg.register_view(
        DisplayView(
            level="session",
            name="results",
            entries=[
                ("group", "provenance"),
                ("group", "inventory"),
            ],
            description=(
                "Operational session provenance summary "
                "showing execution inventory and "
                "completion status."
            ),
        )
    )

    # =====================================================
    # RUN VIEWS
    # =====================================================

    reg.register_view(
        DisplayView(
            level="run",
            name="results",
            entries=[
                ("group", "identity"),
                ("group", "execution"),
                ("group", "planning"),
                ("group", "outcomes"),
            ],
            description="Default run results view.",
        )
    )

    reg.register_view(
        DisplayView(
            level="run",
            name="timing",
            entries=[
                ("group", "identity"),
                ("group", "timing"),
            ],
            description="Default run timing.",
        )
    )

    reg.register_view(
        DisplayView(
            level="run",
            name="run",
            entries=[
                ("group", "identity"),
                ("group", "execution"),
                ("group", "overrides"),
            ],
            description="Compact run execution view.",
        )
    )

    reg.register_view(
        DisplayView(
            level="run",
            name="balances",
            entries=[
                ("group", "identity"),
                ("group", "balances"),
            ],
            description=(
                "Household balance sheet summary "
                "including retirement savings structure, "
                "fixed assets, debts, net worth, "
                "and guaranteed retirement income."
            ),
        )
    )
    # =====================================================
    # CATALOG VIEWS
    # =====================================================

    reg.register_view(
        DisplayView(
            level="catalog",
            name="summary",
            entries=[
                "field_name",
                "owner",
                "semantic_domain",
                "projection_kind",
                "source",
                "description",
            ],
            description=(
                "High-level catalog ontology summary "
                "showing canonical variable identity, "
                "semantic ownership, analytical role, "
                "projection classification, runtime "
                "materialization source, and semantic "
                "description."
            ),
        )
    )

    reg.register_view(
        DisplayView(
            level="catalog",
            name="ontology",
            entries=[
                "field_name",
                "owner",
                "semantic_domain",
                "value_origin",
                "projection_kind",
                "materialization_level",
                "description",
            ],
            description=(
                "Canonical ontology view showing the "
                "semantic classification of variables "
                "across decision, design, and execution "
                "domains, including ownership, origin, "
                "projection semantics, and runtime "
                "materialization level."
            ),
        )
    )

    reg.register_view(
        DisplayView(
            level="catalog",
            name="provenance",
            entries=[
                "field_name",
                "owner",
                "value_origin",
                "projection_kind",
                "materialization_level",
                "source",
                "path",
                "provenance_depth",
            ],
            description=(
                "Provenance-oriented catalog view "
                "showing how variables materialize "
                "through runtime systems, including "
                "their origin, projection lineage, "
                "storage source, canonical path, and "
                "provenance chain depth."
            ),
        )
    )

    reg.register_view(
        DisplayView(
            level="catalog",
            name="aggregates",
            entries=[
                "field_name",
                "projection_kind",
                "derived_from",
                "value_origin",
                "materialization_level",
                "description",
            ],
            description=(
                "Aggregate and derived variable view "
                "showing statistical projections, "
                "derived lineage relationships, and "
                "analytical summarization semantics."
            ),
        )
    )

    reg.register_view(
        DisplayView(
            level="catalog",
            name="paths",
            entries=[
                "field_name",
                "source",
                "path",
                "owner",
                "semantic_domain",
            ],
            description=(
                "Low-level runtime storage mapping "
                "view showing canonical variable names, "
                "runtime storage domains, internal "
                "materialization paths, and ontology "
                "ownership classifications."
            ),
        )
    )

    reg.register_view(
        DisplayView(
            level="catalog",
            name="debug",
            entries=[
                "field_name",
                "layer",
                "owner",
                "semantic_domain",
                "value_origin",
                "projection_kind",
                "materialization_level",
                "source",
                "path",
                "derived_from",
                "provenance_depth",
                "description",
            ],
            description=(
                "Comprehensive debugging and ontology "
                "inspection view exposing all major "
                "catalog semantic dimensions, lineage "
                "metadata, provenance structure, and "
                "runtime materialization metadata."
            ),
        )
    )
