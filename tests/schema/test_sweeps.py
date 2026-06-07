from __future__ import annotations


def test_sweep_fields_registered(
    schema_registry,
):
    """
    Sweep fields are discoverable.
    """

    sweep_fields = [
        f
        for f in schema_registry
        if getattr(
            f,
            "source",
            None,
        )
        == "sweep"
    ]

    assert sweep_fields


def test_sweep_fields_expand(
    schema_registry,
):
    """
    Sweep variables must expand
    into canonical variables.
    """

    sweep_fields = [
        f
        for f in schema_registry
        if getattr(
            f,
            "source",
            None,
        )
        == "sweep"
    ]

    for field in sweep_fields:
        assert field.expands_to


def test_sweep_targets_exist(
    schema_registry,
):
    """
    All sweep expansion targets
    must exist in schema registry.
    """

    sweep_fields = [
        f
        for f in schema_registry
        if getattr(
            f,
            "source",
            None,
        )
        == "sweep"
    ]

    print()

    print(sorted(schema_registry.names()))

    for field in sweep_fields:
        for target in field.expands_to:
            assert schema_registry.exists(target)
