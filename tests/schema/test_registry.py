# tests/schema/test_registry.py


def test_register_and_get_field():
    from owlroost.schema.registry import FieldSpec, SchemaRegistry

    reg = SchemaRegistry()

    field = FieldSpec(
        name="foo",
        dtype=int,
        path=("foo",),
    )

    reg.register(field)

    result = reg.get("foo")

    assert result.name == "foo"
    assert result.dtype == int
    assert result.path == ("foo",)


def test_registry_overwrites_field():
    from owlroost.schema.registry import FieldSpec, SchemaRegistry

    reg = SchemaRegistry()

    reg.register(FieldSpec("foo", int))
    reg.register(FieldSpec("foo", float))

    assert reg.get("foo").dtype == float
