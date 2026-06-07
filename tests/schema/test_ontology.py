from __future__ import annotations

REQUIRED_ONTOLOGY_FIELDS = [
    "owner",
    "semantic_domain",
    "value_origin",
    "projection_kind",
    "analytic_kind",
    "materialization_level",
    "node_type",
]


def test_all_fields_have_complete_ontology(
    schema_registry,
):
    """
    Every registered schema field
    should carry complete ontology.
    """

    for field in schema_registry:
        for attr in REQUIRED_ONTOLOGY_FIELDS:
            value = getattr(
                field,
                attr,
                None,
            )

            assert value is not None, f"{field.name}: missing {attr}"
