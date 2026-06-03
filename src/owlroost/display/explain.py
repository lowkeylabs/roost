# src/owlroost/display/explain.py

"""
Display explanation helpers.

Notes
-----
Owns display-layer explanation rendering.

Architectural Invariant
-----------------------

The explain system is catalog-driven.

Explanation rendering consumes metadata
already materialized into:

    - CatalogSpec
    - DisplayField

This module does NOT perform:

    - schema lookups
    - catalog synthesis
    - OWL introspection
    - registry traversal

It only renders metadata already attached
to the field being displayed.
"""

from __future__ import annotations

from collections.abc import Iterable
from pprint import pformat

# =========================================================
# Explain Facets
# =========================================================

VALID_EXPLAIN_FACETS = {
    "variables",
    "values",
    "sources",
    "display",
    "provenance",
    "notes",
    "ontology",
    "debug",
    "all",
}


def normalize_explain_facets(
    explain: str | Iterable[str] | None,
) -> set[str]:
    """
    Normalize explain specification.

    Examples
    --------

    None
        -> set()

    "description"
        -> {"description"}

    "ontology,provenance"
        -> {"ontology", "provenance"}

    "all"
        -> {
            "description",
            "ontology",
            "display",
            "provenance",
        }
    """

    if explain is None:
        return set()

    if isinstance(
        explain,
        str,
    ):
        facets = {item.strip() for item in explain.split(",") if item.strip()}
    else:
        facets = {str(item).strip() for item in explain if str(item).strip()}

    if "all" in facets:
        facets.remove(
            "all",
        )

        facets |= {
            "variables",
            "values",
            "sources",
            "display",
            "provenance",
            "ontology",
        }

    return facets & VALID_EXPLAIN_FACETS


# =========================================================
# Rendering Helpers
# =========================================================


def _render_parts(
    parts: list[str],
) -> str:
    """
    Render explanation text.
    """

    parts = [part for part in parts if part]

    return "\n\n".join(
        parts,
    )


# =========================================================
# Facets
# =========================================================


def _values_explanation(
    *,
    field_name: str,
    row_values,
) -> str:
    """
    Value facet.

    Displays the materialized values
    associated with this field.
    """

    def clip(text: str, width: int = 22) -> str:
        return text if len(text) <= width else text[: width - 3] + "..."

    return_str = f"{field_name}: ['" + "','".join([clip(rv) for rv in row_values]) + "']"

    return return_str


def _description_explanation(
    display_field,
) -> str:
    """
    Description facet.
    """

    return (
        getattr(
            display_field,
            "description",
            "",
        )
        or ""
    )


def _sources_explanation(
    catalog_row,
) -> str:
    """
    Source facet.

    Explains both:

        - runtime source
        - semantic origin
    """

    if catalog_row is None:
        return ""

    source = catalog_row.get(
        "source",
    )

    origin = catalog_row.get(
        "value_origin",
    )

    return f"{origin} / {source}"


def _ontology_explanation(
    catalog_row,
) -> str:
    """
    Ontology facet.
    """

    if catalog_row is None:
        return ""

    lines = [
        f"Owner: {catalog_row.get('owner')}",
        f"Domain: {catalog_row.get('semantic_domain')}",
        f"Origin: {catalog_row.get('value_origin')}",
        f"Projection: {catalog_row.get('projection_kind')}",
        f"Analytic: {catalog_row.get('analytic_kind')}",
        f"Level: {catalog_row.get('materialization_level')}",
        f"Type: {catalog_row.get('node_type')}",
    ]

    derived_from = (
        catalog_row.get(
            "derived_from",
            [],
        )
        or []
    )

    if derived_from:
        lines.append(
            "Derived From: "
            + ", ".join(
                derived_from,
            )
        )

    return "\n".join(
        lines,
    )


def _display_explanation(
    display_field,
) -> str:
    """
    Display facet.
    """

    if display_field is None:
        return ""

    lines = []

    profiles = getattr(
        display_field,
        "profiles",
        {},
    )

    if profiles:
        profile_lines = []

        for name, profile in sorted(
            profiles.items(),
        ):
            label = (
                getattr(
                    profile,
                    "label",
                    "",
                )
                or ""
            )

            label = label.replace(
                "\n",
                "\\n",
            )

            profile_lines.append(
                f"{name}({label})",
            )

        lines.append(
            "Profiles: "
            + ", ".join(
                profile_lines,
            )
        )

    return "\n".join(
        lines,
    )


def _provenance_explanation(
    catalog_row,
) -> str:
    """
    Provenance facet.
    """

    if catalog_row is None:
        return ""

    chain = (
        catalog_row.get(
            "provenance_chain",
            [],
        )
        or []
    )

    if not chain:
        return ""

    lines = []

    origin_file = catalog_row.get(
        "origin_file",
    )

    defined_in = catalog_row.get(
        "defined_in",
    )

    if origin_file:
        lines.append(
            f"Origin File: {origin_file}",
        )

    if defined_in:
        lines.append(
            f"Defined In: {defined_in}",
        )

    lines.append(
        "",
    )

    for event in chain:
        operation = event.get(
            "operation",
        )

        if hasattr(
            operation,
            "value",
        ):
            operation = operation.value

        lines.append(
            f"{event.get('stage')}:{operation}",
        )

    return "\n".join(
        lines,
    )


def _debug_explanation(
    *,
    display_field,
    catalog_row,
) -> str:
    """
    Debug facet.
    """

    return pformat(
        {
            "catalog_row": catalog_row,
            "display_field": vars(
                display_field,
            )
            if display_field
            else None,
        },
        width=100,
        sort_dicts=False,
    )


# =========================================================
# Explanation Builder
# =========================================================


def build_field_explanation(
    *,
    display_field,
    catalog_row=None,
    explain_facets: set[str],
    row_values=None,
) -> str:
    """
    Build explanation text.

    Notes
    -----
    Consumes already-materialized:

        - CatalogSpec
        - DisplayField

    No registry lookups occur here.
    """

    if not explain_facets:
        return ""

    parts: list[str] = []

    if "variables" in explain_facets and display_field is not None:
        parts.append(
            _description_explanation(
                display_field,
            )
        )

    if "values" in explain_facets:
        parts.append(
            _values_explanation(
                field_name=display_field.field_name,
                row_values=row_values,
            )
        )

    if "sources" in explain_facets and catalog_row is not None:
        parts.append(
            _sources_explanation(
                catalog_row,
            )
        )

    if "display" in explain_facets and display_field is not None:
        parts.append(
            _display_explanation(
                display_field,
            )
        )

    if "ontology" in explain_facets and catalog_row is not None:
        parts.append(
            _ontology_explanation(
                catalog_row,
            )
        )

    if "provenance" in explain_facets and catalog_row is not None:
        parts.append(
            _provenance_explanation(
                catalog_row,
            )
        )

    if "debug" in explain_facets:
        parts.append(
            _debug_explanation(
                display_field=display_field,
                catalog_row=catalog_row,
            )
        )

    return _render_parts(
        parts,
    )
