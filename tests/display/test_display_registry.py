# tests/display/test_registry.py

from __future__ import annotations

import pytest

from owlroost.display.registry import DisplayRegistry
from owlroost.display.specs import (
    DisplayField,
    DisplayGroup,
    DisplayProfile,
    ViewSpec,
)

# =========================================================
# Display Fields
# =========================================================


def test_register_display_field():
    reg = DisplayRegistry()

    field = DisplayField(
        field_name="runtime.trial_jobs",
    )

    reg.register_display_field(field)

    loaded = reg.get_display_field("runtime.trial_jobs")

    assert loaded is field


def test_duplicate_display_field_raises():
    reg = DisplayRegistry()

    field1 = DisplayField(
        field_name="runtime.trial_jobs",
    )

    field2 = DisplayField(
        field_name="runtime.trial_jobs",
    )

    reg.register_display_field(field1)

    with pytest.raises(ValueError):
        reg.register_display_field(field2)


def test_missing_display_field_raises():
    reg = DisplayRegistry()

    with pytest.raises(KeyError):
        reg.get_display_field("missing.field")


def test_has_display_field():
    reg = DisplayRegistry()

    field = DisplayField(
        field_name="runtime.trial_jobs",
    )

    reg.register_display_field(field)

    assert reg.has_display_field("runtime.trial_jobs")

    assert not reg.has_display_field("missing.field")


def test_all_display_fields():
    reg = DisplayRegistry()

    reg.register_display_field(
        DisplayField(
            field_name="a",
        )
    )

    reg.register_display_field(
        DisplayField(
            field_name="b",
        )
    )

    fields = reg.all_display_fields()

    names = {f.field_name for f in fields}

    assert names == {"a", "b"}


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

    loaded = reg.get_group("runtime")

    assert loaded is group


def test_duplicate_group_raises():
    reg = DisplayRegistry()

    g1 = DisplayGroup(
        key="runtime",
        entries=[],
    )

    g2 = DisplayGroup(
        key="runtime",
        entries=[],
    )

    reg.register_group(g1)

    with pytest.raises(ValueError):
        reg.register_group(g2)


def test_missing_group_raises():
    reg = DisplayRegistry()

    with pytest.raises(KeyError):
        reg.get_group("missing")


def test_has_group():
    reg = DisplayRegistry()

    reg.register_group(
        DisplayGroup(
            key="runtime",
            entries=[],
        )
    )

    assert reg.has_group("runtime")

    assert not reg.has_group("missing")


# =========================================================
# Views
# =========================================================


def test_register_view():
    reg = DisplayRegistry()

    view = ViewSpec(
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

    v1 = ViewSpec(
        level="case",
        name="basic",
        entries=[],
    )

    v2 = ViewSpec(
        level="case",
        name="basic",
        entries=[],
    )

    reg.register_view(v1)

    with pytest.raises(ValueError):
        reg.register_view(v2)


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
        ViewSpec(
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
        DisplayField(
            field_name="runtime.trial_jobs",
        )
    )

    reg.register_group(
        DisplayGroup(
            key="runtime",
            entries=[],
        )
    )

    reg.register_view(
        ViewSpec(
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
        DisplayField(
            field_name="runtime.trial_jobs",
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
        ViewSpec(
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
        ViewSpec(
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
        DisplayField(
            field_name="runtime.trial_jobs",
        )
    )

    reg.register_view(
        ViewSpec(
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
        ViewSpec(
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
# Repr
# =========================================================


def test_registry_repr():
    reg = DisplayRegistry()

    text = repr(reg)

    assert "DisplayRegistry" in text

    assert "fields=0" in text

    assert "groups=0" in text

    assert "views=0" in text


# =========================================================
# Profiles
# =========================================================


def test_display_field_profiles():
    field = DisplayField(
        field_name="runtime.trial_jobs",
        profiles={
            "table": DisplayProfile(
                label="Jobs",
            ),
            "pivot": DisplayProfile(
                label="Parallel Trial Workers",
            ),
        },
    )

    assert field.profiles["table"].label == "Jobs"

    assert field.profiles["pivot"].label == "Parallel Trial Workers"
