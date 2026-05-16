# src/owlroost/display/explain.py

from __future__ import annotations

from owlroost.display.generated.owl_parameter_docs import (
    OWL_PARAMETER_DOCS,
)
from owlroost.display.specs import DisplayField, ExplainSpec

# =========================================================
# Explain Facets
# =========================================================

EXPLAIN_FACETS = {
    "variables",
    "values",
    "sources",
    "debug",
    "all",
}


def get_generated_explain_data(
    field_name,
):
    """
    Lookup generated OWL metadata for a field.
    """

    return OWL_PARAMETER_DOCS.get(
        field_name,
        {},
    )


def build_effective_explain_spec(
    display_field,
):
    """
    Merge generated OWL docs with local overrides.

    Priority:
        local ExplainSpec > generated metadata
    """

    generated = get_generated_explain_data(display_field.field_name)

    local = display_field.explain

    spec = ExplainSpec(
        variable=generated.get("variable"),
        units=generated.get("units"),
        notes=generated.get("notes"),
        sources=[],
    )

    # -------------------------------------------------
    # Local overrides
    # -------------------------------------------------

    if local is not None:
        if local.variable:
            spec.variable = local.variable

        if local.value:
            spec.value = local.value

        if local.units:
            spec.units = local.units

        if local.notes:
            spec.notes = local.notes

        if local.sources:
            spec.sources.extend(local.sources)

    return spec


def render_explanation(
    display_field,
    facets,
):
    """
    Build explanation text for a field.
    """

    spec = build_effective_explain_spec(display_field)

    chunks = []

    # =================================================
    # VARIABLES
    # =================================================

    if "variables" in facets:
        if spec.variable:
            chunks.append(spec.variable)

        elif "debug" in facets:
            chunks.append("[missing variable explanation]")

    # =================================================
    # VALUES
    # =================================================

    if "values" in facets:
        if spec.value:
            chunks.append(spec.value)

        elif spec.units:
            chunks.append(f"Units: {spec.units}")

        elif "debug" in facets:
            chunks.append("[missing value explanation]")

    # =================================================
    # SOURCES
    # =================================================

    if "sources" in facets:
        if spec.sources:
            chunks.append("Sources: " + ", ".join(spec.sources))

        elif "debug" in facets:
            chunks.append("[missing source metadata]")

    # =================================================
    # NOTES
    # =================================================

    if spec.notes:
        chunks.append(spec.notes)

    return "\n\n".join(chunks)


# =========================================================
# Facet Normalization
# =========================================================


def normalize_explain_facets(
    explain,
):
    """
    Normalize explain option into a set of facets.

    Examples
    --------

    None
        -> set()

    "variables"
        -> {"variables"}

    "variables,values"
        -> {"variables", "values"}

    {"variables", "debug"}
        -> {"variables", "debug"}

    "all"
        -> {"variables", "values", "sources", "debug"}
    """

    # -----------------------------------------------------
    # None / disabled
    # -----------------------------------------------------

    if not explain:
        return set()

    # -----------------------------------------------------
    # String input
    # -----------------------------------------------------

    if isinstance(explain, str):
        explain = {x.strip() for x in explain.split(",") if x.strip()}

    # -----------------------------------------------------
    # Normalize set
    # -----------------------------------------------------

    explain = set(explain)

    # -----------------------------------------------------
    # Expand "all"
    # -----------------------------------------------------

    if "all" in explain:
        explain = {
            "variables",
            "values",
            "sources",
            "debug",
        }

    # -----------------------------------------------------
    # Validate
    # -----------------------------------------------------

    invalid = explain - EXPLAIN_FACETS

    if invalid:
        invalid_str = ", ".join(sorted(invalid))

        raise ValueError(f"Invalid explain facets: {invalid_str}")

    return explain


# =========================================================
# Explanation Builders
# =========================================================


def build_field_explanation(
    display_field: DisplayField,
    explain_facets,
):
    """
    Build explanation text for a display field.

    Parameters
    ----------
    display_field
        DisplayField specification.

    explain_facets
        Normalized explain facet set.

    Returns
    -------
    str
        Human-readable explanation text.
    """

    if not explain_facets:
        return ""

    explain = display_field.explain

    parts = []

    # =====================================================
    # Variables
    # =====================================================

    if "variables" in explain_facets:
        variable_text = None

        # ---------------------------------------------
        # Preferred v2 ExplainSpec
        # ---------------------------------------------

        if explain is not None and explain.variable:
            variable_text = explain.variable

        # ---------------------------------------------
        # Backward-compatible description
        # ---------------------------------------------

        elif display_field.description:
            variable_text = display_field.description

        if variable_text:
            parts.append(variable_text)

    # =====================================================
    # Values
    # =====================================================

    if "values" in explain_facets and explain is not None and explain.value:
        parts.append(f"Value: {explain.value}")

    # =====================================================
    # Sources
    # =====================================================

    if "sources" in explain_facets and explain is not None and explain.sources:
        source_text = ", ".join(explain.sources)

        parts.append(f"Sources: {source_text}")

    # =====================================================
    # Units
    # =====================================================

    if "values" in explain_facets and explain is not None and explain.units:
        parts.append(f"Units: {explain.units}")

    # =====================================================
    # Notes
    # =====================================================

    if "values" in explain_facets and explain is not None and explain.notes:
        parts.append(f"Notes: {explain.notes}")

    # =====================================================
    # Debug
    # =====================================================

    if "debug" in explain_facets:
        missing = []

        # ---------------------------------------------
        # Variable definition
        # ---------------------------------------------

        has_variable = False

        if explain is not None and explain.variable:
            has_variable = True

        elif display_field.description:
            has_variable = True

        if not has_variable:
            missing.append("variable")

        # ---------------------------------------------
        # Value explanation
        # ---------------------------------------------

        if explain is None or not explain.value:
            missing.append("value")

        # ---------------------------------------------
        # Sources
        # ---------------------------------------------

        if explain is None or not explain.sources:
            missing.append("sources")

        # ---------------------------------------------
        # Units
        # ---------------------------------------------

        if explain is None or not explain.units:
            missing.append("units")

        if missing:
            parts.append("Missing: " + ", ".join(missing))

    # =====================================================
    # Final
    # =====================================================

    return "\n\n".join(parts)
