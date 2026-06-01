from __future__ import annotations

from owlroost.schema.specs import (
    FieldSpec,
)


def test_path_normalizes_to_empty_tuple():
    field = FieldSpec(
        name="test",
        path=None,
    )

    assert field.path == ()


def test_default_source_is_input():
    field = FieldSpec(
        name="test",
    )

    assert field.source == "input"


def test_default_profiles_dict():
    field = FieldSpec(
        name="test",
    )

    assert field.profiles == {}
