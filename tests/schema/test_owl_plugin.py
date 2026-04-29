# tests/schema/test_owl_plugin.py


def test_owl_plugin_registers_fields():
    from owlroost.schema.plugins.owl import OwlSchemaPlugin
    from owlroost.schema.registry import SchemaRegistry

    reg = SchemaRegistry()
    OwlSchemaPlugin().register(reg)

    field = reg.get("basic_info.status")

    assert field.name == "basic_info.status"
    assert field.source == "input"


def test_owl_plugin_registers_nested_fields():
    from owlroost.schema.plugins.owl import OwlSchemaPlugin
    from owlroost.schema.registry import SchemaRegistry

    reg = SchemaRegistry()
    OwlSchemaPlugin().register(reg)

    # nested field
    field = reg.get("rates_selection.method")

    assert field.name == "rates_selection.method"
