# tests/display/test_materialize_case.py

from __future__ import annotations

from owlroost.display.materialize import (
    expand_view_entries,
    materialize_view,
)
from owlroost.display.registry import (
    DisplayRegistry,
)
from owlroost.display.specs import (
    DisplayField,
    DisplayGroup,
    DisplayProfile,
    ViewSpec,
)
from owlroost.display.table import (
    RoostTable,
)

# =========================================================
# Fake Dataset
# =========================================================


class FakeDataset:
    def __init__(self, rows):
        self.rows = rows


# =========================================================
# Registry Builder
# =========================================================


def build_registry():
    reg = DisplayRegistry()

    # -----------------------------------------------------
    # Fields
    # -----------------------------------------------------

    reg.register_display_field(
        DisplayField(
            field_name="case_name",
            profiles={
                "table": DisplayProfile(
                    label="Case",
                )
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="description",
            profiles={
                "table": DisplayProfile(
                    label="Description",
                )
            },
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="runtime.trial_jobs",
            profiles={
                "table": DisplayProfile(
                    label="Trial Jobs",
                    content_align="right",
                )
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
    # View
    # -----------------------------------------------------

    reg.register_view(
        ViewSpec(
            level="case",
            name="basic",
            entries=[
                ("group", "identity"),
                "runtime.trial_jobs",
            ],
        )
    )

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
        "case_name",
        "description",
        "runtime.trial_jobs",
    ]


# =========================================================
# materialize_view
# =========================================================


def test_materialize_returns_table():
    reg = build_registry()

    ds = FakeDataset(rows=[])

    table = materialize_view(
        dataset=ds,
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

    ds = FakeDataset(
        rows=[
            {
                "_inputs": {
                    "case_name": "alpha",
                    "description": "First case",
                    "runtime": {
                        "trial_jobs": 4,
                    },
                }
            }
        ]
    )

    table = materialize_view(
        dataset=ds,
        registry=reg,
        level="case",
        view_name="basic",
    )

    assert len(table.columns) == 3


def test_materialize_column_labels():
    reg = build_registry()

    ds = FakeDataset(
        rows=[
            {
                "_inputs": {
                    "case_name": "alpha",
                    "description": "First case",
                    "runtime": {
                        "trial_jobs": 4,
                    },
                }
            }
        ]
    )

    table = materialize_view(
        dataset=ds,
        registry=reg,
        level="case",
        view_name="basic",
    )

    labels = [c.label for c in table.columns]

    assert labels == [
        "Case",
        "Description",
        "Trial Jobs",
    ]


def test_materialize_column_alignment():
    reg = build_registry()

    ds = FakeDataset(
        rows=[
            {
                "_inputs": {
                    "case_name": "alpha",
                    "description": "First case",
                    "runtime": {
                        "trial_jobs": 4,
                    },
                }
            }
        ]
    )

    table = materialize_view(
        dataset=ds,
        registry=reg,
        level="case",
        view_name="basic",
    )

    aligns = [c.content_align for c in table.columns]

    assert aligns == [
        "left",
        "left",
        "right",
    ]


def test_materialize_rows():
    reg = build_registry()

    ds = FakeDataset(
        rows=[
            {
                "_inputs": {
                    "case_name": "alpha",
                    "description": "First case",
                    "runtime": {
                        "trial_jobs": 4,
                    },
                }
            },
            {
                "_inputs": {
                    "case_name": "beta",
                    "description": "Second case",
                    "runtime": {
                        "trial_jobs": 8,
                    },
                }
            },
        ]
    )

    table = materialize_view(
        dataset=ds,
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


def test_materialize_empty_dataset():
    reg = build_registry()

    ds = FakeDataset(rows=[])

    table = materialize_view(
        dataset=ds,
        registry=reg,
        level="case",
        view_name="basic",
    )

    assert table.rows == []


def test_materialize_missing_value():
    reg = build_registry()

    ds = FakeDataset(
        rows=[
            {
                "_inputs": {
                    "case_name": "alpha",
                }
            }
        ]
    )

    table = materialize_view(
        dataset=ds,
        registry=reg,
        level="case",
        view_name="basic",
    )

    assert table.rows == [
        [
            "alpha",
            None,
            None,
        ]
    ]


def test_materialize_missing_profile_uses_defaults():
    reg = DisplayRegistry()

    reg.register_display_field(
        DisplayField(
            field_name="x",
        )
    )

    reg.register_view(
        ViewSpec(
            level="case",
            name="basic",
            entries=["x"],
        )
    )

    ds = FakeDataset(
        rows=[
            {
                "_inputs": {
                    "x": 123,
                }
            }
        ]
    )

    table = materialize_view(
        dataset=ds,
        registry=reg,
        level="case",
        view_name="basic",
    )

    col = table.columns[0]

    assert col.label == "x"

    assert col.content_align == "left"


def test_materialize_unknown_entry_raises():
    reg = DisplayRegistry()

    with_exception = False

    try:
        expand_view_entries(
            reg,
            [{"bad": "entry"}],
        )

    except ValueError:
        with_exception = True

    assert with_exception
