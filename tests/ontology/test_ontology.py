# tests/ontology/test_ontology.py

from __future__ import annotations

from dataclasses import fields
from typing import get_args

from owlroost.catalog.ontology import (
    ONTOLOGY_DIMENSIONS,
    OntologySpec,
)

ONTOLOGY_FIELDS = {
    "owner",
    "semantic_domain",
    "value_origin",
    "projection_kind",
    "analytic_kind",
    "materialization_level",
    "node_type",
}


def test_all_ontology_spec_fields_registered():
    """
    Every ontology dimension defined on
    OntologySpec must appear in the
    ontology registry.
    """

    registered = {d.field_name for d in ONTOLOGY_DIMENSIONS}

    assert registered == ONTOLOGY_FIELDS


def test_all_registered_dimensions_exist_on_spec():
    """
    Registry dimensions must correspond
    to real OntologySpec attributes.
    """

    spec_fields = {
        f.name
        for f in fields(
            OntologySpec,
        )
    }

    for dim in ONTOLOGY_DIMENSIONS:
        assert dim.field_name in spec_fields


def test_dimension_names_unique():
    """
    Registry field names must be unique.
    """

    names = [d.field_name for d in ONTOLOGY_DIMENSIONS]

    assert len(names) == len(set(names))


def test_dimension_labels_unique():
    """
    Dashboard labels should be unique.
    """

    labels = [d.label for d in ONTOLOGY_DIMENSIONS]

    assert len(labels) == len(set(labels))


def test_dimension_cli_names_unique():
    """
    CLI aliases should be unique.
    """

    names = [d.cli_name for d in ONTOLOGY_DIMENSIONS]

    assert len(names) == len(set(names))


def test_dimension_descriptions_present():
    """
    Every ontology dimension should
    provide user-facing documentation.
    """

    for dim in ONTOLOGY_DIMENSIONS:
        assert dim.description
        assert dim.description.strip()


def test_dimension_value_types_not_empty():
    """
    Every ontology dimension must expose
    at least one allowed value.
    """

    for dim in ONTOLOGY_DIMENSIONS:
        values = get_args(
            dim.values_type,
        )

        if values:
            assert len(values) > 0
        else:
            # StrEnum-based dimensions
            assert len(list(dim.values_type)) > 0


def test_dimension_count_matches_spec():
    """
    Registry should contain exactly one
    entry for every ontology field.
    """

    assert len(ONTOLOGY_DIMENSIONS) == len(ONTOLOGY_FIELDS)
