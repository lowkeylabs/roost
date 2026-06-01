# tests/display/test_registry.py

from __future__ import annotations

import pytest

from owlroost.display.registry import (
    DisplayRegistry,
)
from owlroost.display.specs import (
    DisplayField,
    DisplayGroup,
    DisplayProfile,
    DisplayView,
)

# =========================================================
# Helpers
# =========================================================


def make_field(
    name: str,
    **kwargs,
):
    return DisplayField.field(
        name,
        **kwargs,
    )


# =========================================================
# Display Fields
# =========================================================


def test_register_display_field():
    reg = DisplayRegistry()

    field = make_field(
        "runtime.trial_jobs",
    )

    reg.register_display_field(field)

    loaded = reg.get_display_field(
        "runtime.trial_jobs",
    )

    assert loaded is field


def test_display_field_override():
    reg = DisplayRegistry()

    reg.register_display_field(
        make_field("x"),
    )

    reg.register_display_field(
        make_field(
            "x",
            description="override",
        )
    )

    field = reg.get_display_field(
        "x",
    )

    assert field.description == "override"


def test_missing_display_field_raises():
    reg = DisplayRegistry()

    with pytest.raises(KeyError):
        reg.get_display_field(
            "missing.field",
        )


def test_has_display_field():
    reg = DisplayRegistry()

    reg.register_display_field(
        make_field(
            "runtime.trial_jobs",
        )
    )

    assert reg.has_display_field(
        "runtime.trial_jobs",
    )

    assert not reg.has_display_field(
        "missing.field",
    )


def test_all_display_fields():
    reg = DisplayRegistry()

    reg.register_display_field(
        make_field("a"),
    )

    reg.register_display_field(
        make_field("b"),
    )

    fields = reg.all_display_fields()

    names = {field.field_name for field in fields}

    assert names == {
        "a",
        "b",
    }


def test_all_alias():
    reg = DisplayRegistry()

    reg.register_display_field(
        make_field("a"),
    )

    fields = reg.all()

    assert len(fields) == 1

    assert fields[0].field_name == "a"


# =========================================================
# Groups
# =========================================================


def test_register_group():
    reg = DisplayRegistry()

    group = DisplayGroup(
        key="runtime",
        entries=[
            "runtime.trial_jobs",
        ],
    )

    reg.register_group(group)

    loaded = reg.get_group(
        "runtime",
    )

    assert loaded is group


def test_duplicate_group_raises():
    reg = DisplayRegistry()

    reg.register_group(
        DisplayGroup(
            key="runtime",
            entries=[],
        )
    )

    with pytest.raises(ValueError):
        reg.register_group(
            DisplayGroup(
                key="runtime",
                entries=[],
            )
        )


def test_missing_group_raises():
    reg = DisplayRegistry()

    with pytest.raises(KeyError):
        reg.get_group(
            "missing",
        )


def test_has_group():
    reg = DisplayRegistry()

    reg.register_group(
        DisplayGroup(
            key="runtime",
            entries=[],
        )
    )

    assert reg.has_group(
        "runtime",
    )

    assert not reg.has_group(
        "missing",
    )


# =========================================================
# Views
# =========================================================


def test_register_view():
    reg = DisplayRegistry()

    view = DisplayView(
        level="case",
        name="basic",
        entries=[],
    )

    reg.register_view(view)

    loaded = reg.get_view(
        "case",
        "basic",
    )

    assert loaded is view


def test_duplicate_view_raises():
    reg = DisplayRegistry()

    reg.register_view(
        DisplayView(
            level="case",
            name="basic",
            entries=[],
        )
    )

    with pytest.raises(ValueError):
        reg.register_view(
            DisplayView(
                level="case",
                name="basic",
                entries=[],
            )
        )


def test_missing_view_raises():
    reg = DisplayRegistry()

    with pytest.raises(KeyError):
        reg.get_view(
            "case",
            "missing",
        )


def test_has_view():
    reg = DisplayRegistry()

    reg.register_view(
        DisplayView(
            level="case",
            name="basic",
            entries=[],
        )
    )

    assert reg.has_view(
        "case",
        "basic",
    )

    assert not reg.has_view(
        "case",
        "missing",
    )


# =========================================================
# Summary
# =========================================================


def test_registry_summary_counts():
    reg = DisplayRegistry()

    reg.register_display_field(
        make_field(
            "runtime.trial_jobs",
        )
    )

    reg.register_group(
        DisplayGroup(
            key="runtime",
            entries=[],
        )
    )

    reg.register_view(
        DisplayView(
            level="case",
            name="basic",
            entries=[],
        )
    )

    summary = reg.summary()

    assert summary == {
        "display_fields": 1,
        "groups": 1,
        "views": 1,
    }


# =========================================================
# Validation
# =========================================================


def test_validate_group_field_reference():
    reg = DisplayRegistry()

    reg.register_display_field(
        make_field(
            "runtime.trial_jobs",
        )
    )

    reg.register_group(
        DisplayGroup(
            key="runtime",
            entries=[
                "runtime.trial_jobs",
            ],
        )
    )

    reg.validate()


def test_validate_missing_group_field_raises():
    reg = DisplayRegistry()

    reg.register_group(
        DisplayGroup(
            key="runtime",
            entries=[
                "missing.field",
            ],
        )
    )

    with pytest.raises(ValueError):
        reg.validate()


def test_validate_view_group_reference():
    reg = DisplayRegistry()

    reg.register_group(
        DisplayGroup(
            key="runtime",
            entries=[],
        )
    )

    reg.register_view(
        DisplayView(
            level="case",
            name="basic",
            entries=[
                ("group", "runtime"),
            ],
        )
    )

    reg.validate()


def test_validate_missing_view_group_raises():
    reg = DisplayRegistry()

    reg.register_view(
        DisplayView(
            level="case",
            name="basic",
            entries=[
                ("group", "missing_group"),
            ],
        )
    )

    with pytest.raises(ValueError):
        reg.validate()


def test_validate_view_field_reference():
    reg = DisplayRegistry()

    reg.register_display_field(
        make_field(
            "runtime.trial_jobs",
        )
    )

    reg.register_view(
        DisplayView(
            level="case",
            name="basic",
            entries=[
                ("field", "runtime.trial_jobs"),
            ],
        )
    )

    reg.validate()


def test_validate_missing_view_field_raises():
    reg = DisplayRegistry()

    reg.register_view(
        DisplayView(
            level="case",
            name="basic",
            entries=[
                ("field", "missing.field"),
            ],
        )
    )

    with pytest.raises(ValueError):
        reg.validate()


# =========================================================
# Synthetic Fields
# =========================================================


def test_register_synthetic_field():
    reg = DisplayRegistry()

    field = DisplayField.field(
        "display.net_worth",
        derived_from=[
            "display.total_savings",
        ],
    )

    reg.register_display_field(
        field,
    )

    loaded = reg.get_display_field(
        "display.net_worth",
    )

    assert loaded.is_synthetic


def test_synthetic_field_defaults():
    field = DisplayField.field(
        "display.net_worth",
        derived_from=[
            "display.total_savings",
        ],
    )

    assert field.is_synthetic

    assert field.owner == "ROOST"

    assert field.semantic_domain == "decision"

    assert field.value_origin == "roost-computed"

    assert field.projection_kind == "synthetic"

    assert field.analytic_kind == "synthetic"

    assert field.materialization_level == "case"


def test_synthetic_field_preserves_lineage():
    field = DisplayField.field(
        "display.net_worth",
        derived_from=[
            "display.total_savings",
            "display.net_hfp_assets",
        ],
    )

    assert field.derived_from == [
        "display.total_savings",
        "display.net_hfp_assets",
    ]


def test_display_fn_implies_synthetic():
    def compute(row):
        return 123

    field = DisplayField.field(
        "display.net_worth",
        display_fn=compute,
    )

    assert field.is_synthetic


def test_projection_kind_implies_synthetic():
    field = DisplayField.field(
        "display.net_worth",
        projection_kind="synthetic",
    )

    assert field.is_synthetic


# =========================================================
# Ordinary Fields
# =========================================================


def test_ordinary_field_not_synthetic():
    field = DisplayField.field(
        "solver_options.bequest",
    )

    assert not field.is_synthetic


# =========================================================
# Profiles
# =========================================================


def test_display_field_profiles():
    field = DisplayField.field(
        "runtime.trial_jobs",
        profiles={
            "table": DisplayProfile(
                label="Jobs",
            ),
            "pivot": DisplayProfile(
                label=("Parallel Trial Workers"),
            ),
        },
    )

    assert field.profiles["table"].label == "Jobs"

    assert field.profiles["pivot"].label == "Parallel Trial Workers"


# =========================================================
# Repr
# =========================================================


def test_registry_repr():
    reg = DisplayRegistry()

    text = repr(reg)

    assert "DisplayRegistry" in text

    assert "fields=0" in text

    assert "groups=0" in text

    assert "views=0" in text
