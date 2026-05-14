# tests/schema/test_registry.py


import pytest


def test_register_and_get_field():
    from owlroost.schema.registry import FieldSpec, SchemaRegistry

    reg = SchemaRegistry()

    field = FieldSpec(
        name="foo",
        dtype=int,
        path=("foo",),
        source="input",
        level="trial",
    )

    reg.register(field)

    result = reg.get("foo")

    assert str(result.name) == "foo"
    assert result.dtype == int
    assert result.path == ("foo",)


def test_registry_rejects_duplicate_field():
    from owlroost.schema.registry import FieldSpec, SchemaRegistry

    reg = SchemaRegistry()

    reg.register(FieldSpec("a", int, path="path", source="input", level="trial"))

    with pytest.raises(ValueError):
        reg.register(FieldSpec("a", int, path="path", source="input", level="trial"))
