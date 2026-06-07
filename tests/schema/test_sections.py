from __future__ import annotations


def test_roost_sections_registered(
    schema_registry,
):
    """
    At least one ROOST section field exists.
    """

    roost_fields = [
        f
        for f in schema_registry
        if getattr(
            f,
            "owner",
            None,
        )
        == "ROOST"
    ]

    assert roost_fields


def test_section_fields_have_paths(
    schema_registry,
):
    """
    Registered fields should carry paths.
    """

    for field in schema_registry:
        assert isinstance(
            field.path,
            tuple,
        )
