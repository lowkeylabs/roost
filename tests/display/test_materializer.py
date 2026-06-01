from __future__ import annotations

from owlroost.display.materializers.materialize import (
    expand_view_entries,
    materialize_view,
)
from owlroost.display.registry import (
    DisplayRegistry,
)
from owlroost.display.renderers.specs import (
    RoostTable,
)
from owlroost.display.specs import (
    DisplayField,
    DisplayGroup,
    DisplayProfile,
    DisplayView,
)

# =========================================================
# Registry Builder
# =========================================================


def build_registry():
    reg = DisplayRegistry()

    # -----------------------------------------------------
    # Fields
    # -----------------------------------------------------

    reg.register_display_field(
        DisplayField.field(
            "case_name",
            profiles={
                "table": DisplayProfile(
                    label="Case",
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField.field(
            "description",
            profiles={
                "table": DisplayProfile(
                    label="Description",
                ),
            },
        )
    )

    reg.register_display_field(
        DisplayField.field(
            "runtime.trial_jobs",
            profiles={
                "table": DisplayProfile(
                    label="Trial Jobs",
                    content_align="right",
                ),
            },
        )
    )

    # -----------------------------------------------------
    # Groups
    # -----------------------------------------------------

    reg.register_group(
        DisplayGroup(
            key="identity",
            entries=[
                "case_name",
                "description",
            ],
        )
    )

    # -----------------------------------------------------
    # Views
    # -----------------------------------------------------

    reg.register_view(
        DisplayView(
            level="case",
            name="basic",
            entries=[
                (
                    "group",
                    "identity",
                ),
                "runtime.trial_jobs",
            ],
        )
    )

    reg.validate()

    return reg


# =========================================================
# expand_view_entries
# =========================================================


def test_expand_view_entries():
    reg = build_registry()

    view = reg.get_view(
        "case",
        "basic",
    )

    fields = expand_view_entries(
        reg,
        view.entries,
    )

    assert fields == [
        {"field": "case_name"},
        {"field": "description"},
        {"field": "runtime.trial_jobs"},
    ]


# =========================================================
# materialize_view
# =========================================================


def test_materialize_returns_table():
    reg = build_registry()

    table = materialize_view(
        rows=[],
        registry=reg,
        level="case",
        view_name="basic",
    )

    assert isinstance(
        table,
        RoostTable,
    )


def test_materialize_column_count():
    reg = build_registry()

    rows = [
        {
            "_inputs": {
                "case_name": "alpha",
                "description": "First case",
                "runtime": {
                    "trial_jobs": 4,
                },
            },
        },
    ]

    table = materialize_view(
        rows=rows,
        registry=reg,
        level="case",
        view_name="basic",
    )

    assert len(table.columns) == 3


def test_materialize_column_labels():
    reg = build_registry()

    rows = [
        {
            "_inputs": {
                "case_name": "alpha",
                "description": "First case",
                "runtime": {
                    "trial_jobs": 4,
                },
            },
        },
    ]

    table = materialize_view(
        rows=rows,
        registry=reg,
        level="case",
        view_name="basic",
    )

    labels = [column.label for column in table.columns]

    assert labels == [
        "Case",
        "Description",
        "Trial Jobs",
    ]


def test_materialize_column_alignment():
    reg = build_registry()

    rows = [
        {
            "_inputs": {
                "case_name": "alpha",
                "description": "First case",
                "runtime": {
                    "trial_jobs": 4,
                },
            },
        },
    ]

    table = materialize_view(
        rows=rows,
        registry=reg,
        level="case",
        view_name="basic",
    )

    aligns = [column.content_align for column in table.columns]

    assert aligns == [
        "left",
        "left",
        "right",
    ]


def test_materialize_rows():
    reg = build_registry()

    rows = [
        {
            "_inputs": {
                "case_name": "alpha",
                "description": "First case",
                "runtime": {
                    "trial_jobs": 4,
                },
            },
        },
        {
            "_inputs": {
                "case_name": "beta",
                "description": "Second case",
                "runtime": {
                    "trial_jobs": 8,
                },
            },
        },
    ]

    table = materialize_view(
        rows=rows,
        registry=reg,
        level="case",
        view_name="basic",
    )

    assert table.rows == [
        [
            "alpha",
            "First case",
            4,
        ],
        [
            "beta",
            "Second case",
            8,
        ],
    ]


def test_materialize_empty_rows():
    reg = build_registry()

    table = materialize_view(
        rows=[],
        registry=reg,
        level="case",
        view_name="basic",
    )

    assert table.rows == []


def test_materialize_missing_value():
    reg = build_registry()

    rows = [
        {
            "_inputs": {
                "case_name": "alpha",
            },
        },
    ]

    table = materialize_view(
        rows=rows,
        registry=reg,
        level="case",
        view_name="basic",
    )

    assert table.rows == [
        [
            "alpha",
            None,
            None,
        ],
    ]


def test_materialize_missing_profile_uses_defaults():
    reg = DisplayRegistry()

    reg.register_display_field(
        DisplayField.field(
            "x",
        )
    )

    reg.register_view(
        DisplayView(
            level="case",
            name="basic",
            entries=[
                "x",
            ],
        )
    )

    reg.validate()

    rows = [
        {
            "_inputs": {
                "x": 123,
            },
        },
    ]

    table = materialize_view(
        rows=rows,
        registry=reg,
        level="case",
        view_name="basic",
    )

    column = table.columns[0]

    assert column.label == "x"

    assert column.content_align == "left"


def test_materialize_unknown_entry_raises():
    reg = DisplayRegistry()

    try:
        expand_view_entries(
            reg,
            [
                {
                    "bad": "entry",
                },
            ],
        )

        assert False

    except ValueError:
        pass
