# tests/display/test_explain.py

from __future__ import annotations

from owlroost.display.explain import (
    build_explanation_cell,
    build_field_explanation,
    parse_explain_request,
)
from owlroost.display.explain.facets import (
    AVAILABLE_EXPLAIN_FACETS,
)

# =========================================================
# Parse Explain Request
# =========================================================


def test_parse_explain_request_none():
    facets, errors = parse_explain_request(
        None,
    )

    assert facets == set()

    assert errors == []


def test_parse_explain_request_single():
    facets, errors = parse_explain_request(
        "variables",
    )

    assert facets == {
        "variables",
    }

    assert errors == []


def test_parse_explain_request_multiple():
    facets, errors = parse_explain_request(
        "variables,ontology",
    )

    assert facets == {
        "variables",
        "ontology",
    }

    assert errors == []


def test_parse_explain_request_unknown():
    facets, errors = parse_explain_request(
        "variables,bogus",
    )

    assert facets == {
        "variables",
    }

    assert errors == [
        "Unknown explain facet: bogus",
    ]


def test_parse_explain_request_all():
    facets, errors = parse_explain_request(
        "all",
    )

    assert errors == []

    assert "variables" in facets

    assert "ontology" in facets

    assert "all" not in facets


# =========================================================
# Facet Discovery
# =========================================================


def test_available_facets_contains_all():
    assert "all" in AVAILABLE_EXPLAIN_FACETS


def test_available_facets_contains_variables():
    assert "variables" in AVAILABLE_EXPLAIN_FACETS


# =========================================================
# Explanation Rendering
# =========================================================


class DummyDisplayField:
    field_name = "example"

    description = "Example description"

    profiles = {}


def test_build_field_explanation_empty():
    text = build_field_explanation(
        display_field=None,
        catalog_row=None,
        explain_facets=set(),
    )

    assert text == ""


def test_build_field_explanation_variables():
    text = build_field_explanation(
        display_field=DummyDisplayField(),
        catalog_row=None,
        explain_facets={
            "variables",
        },
    )

    assert "Example description" in text


def test_build_field_explanation_unknown_facet_ignored():
    text = build_field_explanation(
        display_field=DummyDisplayField(),
        catalog_row=None,
        explain_facets={
            "bogus",
        },
    )

    assert text == ""


# =========================================================
# Explanation Cell Builder
# =========================================================


class DummyRegistry:
    def get_display_field(
        self,
        field_name,
    ):
        assert field_name == "example"

        return DummyDisplayField()


def test_build_explanation_cell_no_facets():
    text = build_explanation_cell(
        field_name="example",
        explain_facets=set(),
    )

    assert text == ""


def test_build_explanation_cell_missing_registry():
    text = build_explanation_cell(
        field_name="example",
        registry=None,
        catalog_index=None,
        explain_facets={
            "variables",
        },
    )

    assert text == ""


def test_build_explanation_cell_success():
    text = build_explanation_cell(
        field_name="example",
        registry=DummyRegistry(),
        catalog_index={},
        explain_facets={
            "variables",
        },
    )

    assert "Example description" in text


def test_build_explanation_cell_handles_registry_failure():
    class BrokenRegistry:
        def get_display_field(
            self,
            field_name,
        ):
            raise RuntimeError(
                "boom",
            )

    text = build_explanation_cell(
        field_name="example",
        registry=BrokenRegistry(),
        catalog_index=None,
        explain_facets={
            "variables",
        },
    )

    assert isinstance(
        text,
        str,
    )


def test_build_explanation_cell_uses_full_field_name():
    class Registry:
        def get_display_field(
            self,
            field_name,
        ):
            return DummyDisplayField()

    catalog_index = {
        "solver_options.bequest": {
            "value_origin": "user-specified",
            "source": "input",
        }
    }

    text = build_explanation_cell(
        field_name="solver_options.bequest",
        registry=Registry(),
        catalog_index=catalog_index,
        explain_facets={
            "sources",
        },
    )

    assert "user-specified" in text


def test_parse_explain_request_multiple_unknown_facets():
    facets, errors = parse_explain_request(
        "variables,bogus,garbage",
    )

    assert facets == {
        "variables",
    }

    assert len(errors) == 2

    assert "bogus" in errors[0]
    assert "garbage" in errors[1]


def test_build_field_explanation_handles_facet_failure(
    monkeypatch,
):
    from owlroost.display.explain.facets import FACETS

    def boom(**kwargs):
        raise RuntimeError(
            "kaboom",
        )

    original = FACETS["variables"]

    FACETS["variables"] = boom

    try:
        text = build_field_explanation(
            display_field=DummyDisplayField(),
            catalog_row=None,
            explain_facets={
                "variables",
            },
        )

        assert "facet error" in text

    finally:
        FACETS["variables"] = original
