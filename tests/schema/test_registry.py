def test_register_and_get_field():
    from owlroost.schema.registry import SchemaRegistry

    reg = SchemaRegistry()
    reg.register("foo", {"type": "int"})

    assert reg.get("foo") == {"type": "int"}
