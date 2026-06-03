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
            "sources",
            "display",
            "provenance",
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
    catalog_spec,
) -> str:
    """
    Source facet.

    Explains both:

        - runtime source
        - semantic origin
    """

    if catalog_spec is None:
        return ""

    lines = []

    source = getattr(
        catalog_spec,
        "source",
        None,
    )

    if source:
        lines.append(f"Source: {source}")

    origin = getattr(
        catalog_spec,
        "value_origin",
        None,
    )

    if origin:
        lines.append(f"Origin: {origin}")

    return "\n".join(
        lines,
    )


def _ontology_explanation(
    catalog_spec,
) -> str:
    """
    Ontology facet.
    """

    lines = [
        f"Owner: {catalog_spec.owner}",
        f"Domain: {catalog_spec.semantic_domain}",
        f"Origin: {catalog_spec.value_origin}",
        f"Projection: {catalog_spec.projection_kind}",
        f"Analytic: {catalog_spec.analytic_kind}",
        f"Level: {catalog_spec.materialization_level}",
        f"Type: {catalog_spec.node_type}",
    ]

    derived_from = getattr(
        catalog_spec,
        "derived_from",
        [],
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

            profile_lines.append(f"{name}({label})")

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
    catalog_spec,
) -> str:
    """
    Provenance facet.
    """

    chain = getattr(
        catalog_spec,
        "provenance_chain",
        [],
    )

    if not chain:
        return ""

    lines = []

    if catalog_spec.origin_file:
        lines.append(f"Origin File: {catalog_spec.origin_file}")

    if catalog_spec.defined_in:
        lines.append(f"Defined In: {catalog_spec.defined_in}")

    lines.append("")

    for event in chain:
        operation = event.operation

        if hasattr(
            operation,
            "value",
        ):
            operation = operation.value

        lines.append(f"{event.stage}:{operation}")

    return "\n".join(
        lines,
    )


def _debug_explanation(
    *,
    display_field,
    catalog_spec,
) -> str:
    """
    Debug facet.
    """

    return pformat(
        {
            "catalog_spec": vars(
                catalog_spec,
            )
            if catalog_spec
            else None,
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
    catalog_spec,
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

    if "sources" in explain_facets and catalog_spec is not None:
        parts.append(
            _sources_explanation(
                catalog_spec,
            )
        )

    if "ontology" in explain_facets and catalog_spec is not None:
        parts.append(
            _ontology_explanation(
                catalog_spec,
            )
        )

    if "display" in explain_facets and display_field is not None:
        parts.append(
            _display_explanation(
                display_field,
            )
        )

    if "provenance" in explain_facets and catalog_spec is not None:
        parts.append(
            _provenance_explanation(
                catalog_spec,
            )
        )

    if "debug" in explain_facets:
        parts.append(
            _debug_explanation(
                display_field=display_field,
                catalog_spec=catalog_spec,
            )
        )

    return _render_parts(
        parts,
    )
