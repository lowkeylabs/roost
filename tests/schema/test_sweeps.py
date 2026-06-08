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


def test_sweep_fields_materialize(
    schema_registry,
):
    """
    Sweep variables must materialize
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
        assert field.materializes_to


def test_sweep_materialization_targets_exist(
    schema_registry,
):
    """
    All sweep materialization targets
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

    for field in sweep_fields:
        for target in field.materializes_to:
            assert schema_registry.exists(
                target,
            )
