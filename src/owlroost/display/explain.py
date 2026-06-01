# src/owlroost/display/explain.py

"""
Display explanation helpers.

Notes
-----
This module owns display-layer explanation
generation used by materializers and renderers.

Architectural Responsibilities
------------------------------

Owns:
    - explain facet normalization
    - explanation text formatting
    - display-layer explanation rendering

Does NOT own:
    - schema metadata
    - OWL documentation
    - catalog synthesis
    - ontology harvesting

Schema and catalog metadata should be
attached to DisplayField objects upstream.
"""

from __future__ import annotations

from collections.abc import Iterable

# =========================================================
# Explain Facets
# =========================================================

VALID_EXPLAIN_FACETS = {
    "variables",
    "sources",
    "notes",
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

    "variables"
        -> {"variables"}

    "variables,sources"
        -> {"variables", "sources"}

    "all"
        -> {"variables", "sources", "notes"}
    """

    if explain is None:
        return set()

    if isinstance(explain, str):
        facets = {item.strip() for item in explain.split(",") if item.strip()}
    else:
        facets = {str(item).strip() for item in explain if str(item).strip()}

    if "all" in facets:
        return {
            "variables",
            "sources",
            "notes",
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

    return "\n".join(parts)


# =========================================================
# Explanation Builder
# =========================================================


def build_field_explanation(
    display_field,
    explain_facets: set[str],
    *,
    row_values: dict | None = None,
) -> str:
    """
    Build explanation text for a display field.

    Notes
    -----
    This function intentionally relies only
    on metadata already attached to the
    DisplayField.

    No schema lookups, catalog lookups,
    or generated documentation loading
    should occur here.
    """

    if not explain_facets:
        return ""

    parts: list[str] = []

    # =====================================================
    # Variable / Description
    # =====================================================

    if "variables" in explain_facets:
        description = getattr(
            display_field,
            "description",
            "",
        )

        if description:
            parts.append(description)

    # =====================================================
    # Source
    # =====================================================

    if "sources" in explain_facets:
        source = getattr(
            display_field,
            "source",
            None,
        )

        if source:
            parts.append(f"Source: {source}")

    # =====================================================
    # Notes
    # =====================================================

    if "notes" in explain_facets:
        notes = getattr(
            display_field,
            "notes",
            "",
        )

        if notes:
            parts.append(notes)

    return _render_parts(parts)
