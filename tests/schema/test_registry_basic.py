# tests/schema/test_registry_basic.py

import pytest


def test_register_and_get_field():
    from owlroost.schema.registry import FieldSpec, SchemaRegistry

    reg = SchemaRegistry()

    field = FieldSpec(
        name="test.field",
        dtype=int,
        path=("test", "field"),
        source="input",
        level="trial",
    )

    reg.register(field)

    retrieved = reg.get("test.field")

    assert retrieved.name == "test.field"
    assert retrieved.dtype == int
    assert retrieved.path == ("test", "field")


def test_registry_rejects_duplicate_field():
    from owlroost.schema.registry import FieldSpec, SchemaRegistry

    reg = SchemaRegistry()

    reg.register(
        FieldSpec(
            "a",
            int,
            source="input",
            level="trial",
        )
    )

    with pytest.raises(ValueError):
        reg.register(
            FieldSpec(
                "a",
                int,
                source="input",
                level="trial",
            )
        )


def test_duplicate_field_error_message():
    import pytest

    from owlroost.schema.registry import FieldSpec, SchemaRegistry

    reg = SchemaRegistry()
    reg.register(
        FieldSpec(
            "a",
            int,
            source="input",
            level="trial",
        )
    )

    with pytest.raises(ValueError) as exc:
        reg.register(
            FieldSpec(
                "a",
                int,
                source="input",
                level="trial",
            )
        )

    assert "Duplicate field registered: a" in str(exc.value)
