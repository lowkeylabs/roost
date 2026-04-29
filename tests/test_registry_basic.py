# tests/schema/test_registry_basic.py


def test_register_and_get_field():
    from owlroost.schema.registry import FieldSpec, SchemaRegistry

    reg = SchemaRegistry()

    field = FieldSpec(
        name="test.field",
        dtype=int,
        path=("test", "field"),
    )

    reg.register(field)

    retrieved = reg.get("test.field")

    assert retrieved.name == "test.field"
    assert retrieved.dtype == int
    assert retrieved.path == ("test", "field")


def test_registry_overwrites_existing_field():
    from owlroost.schema.registry import FieldSpec, SchemaRegistry

    reg = SchemaRegistry()

    reg.register(FieldSpec("a", int))
    reg.register(FieldSpec("a", float))

    assert reg.get("a").dtype == float
