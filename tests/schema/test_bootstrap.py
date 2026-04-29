# tests/schema/test_bootstrap.py


def test_build_registry_contains_core_fields():
    from owlroost.schema.bootstrap import build_registry

    reg = build_registry()

    # OWL field
    field = reg.get("basic_info.names")

    assert field.name == "basic_info.names"
    assert field.source == "input"
