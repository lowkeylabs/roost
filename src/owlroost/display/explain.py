# src/owlroost/display/explain.py

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pprint import pformat

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
    "units",
    "sources",
    "notes",
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


def _build_debug_explanation(
    display_field: DisplayField,
    row_values=None,
) -> str:
    """
    Build detailed debug/introspection output
    for explanation resolution.
    """

    lines = []

    # =====================================================
    # DisplayField
    # =====================================================

    lines.append("DisplayField:")

    if is_dataclass(display_field):
        lines.append(
            pformat(
                asdict(display_field),
                sort_dicts=False,
            )
        )
    else:
        lines.append(repr(display_field))

    # =====================================================
    # ExplainSpec
    # =====================================================

    explain = display_field.explain

    lines.append("\nExplainSpec:")

    if explain is None:
        lines.append("None")

    elif is_dataclass(explain):
        lines.append(
            pformat(
                asdict(explain),
                sort_dicts=False,
            )
        )

    else:
        lines.append(repr(explain))

    # =====================================================
    # Row Values
    # =====================================================

    lines.append("\nRow Values:")

    lines.append(
        pformat(
            row_values,
            sort_dicts=False,
        )
    )

    return "\n".join(lines)


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
            chunks.append("[add variable= to ExplainSpec]")

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
            prefix = "Sources:" if len(spec.sources) > 1 else "Source:"
            chunks.append(f"{prefix} " + ", ".join(spec.sources))

        elif "debug" in facets:
            chunks.append("[missing source metadata]")

    # =================================================
    # NOTES
    # =================================================

    if spec.notes:
        chunks.append(spec.notes)

    return "; ".join(chunks) + "\n"


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
        -> {"variables", "values", "sources", "debug", "units", "notes" }
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

    debug = "debug" in explain

    if "all" in explain:
        explain = {
            "variables",
            "values",
            "units",
            "sources",
            "notes",
        }

    if debug:
        explain.add("debug")

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


def _resolve_explain_facet(
    display_field: DisplayField,
    facet: str,
    row_values=None,
) -> list | str | None:
    """
    Resolve explanation facet using layered precedence.

    Priority:
        1. ExplainSpec override
        2. FieldSpec metadata
        3. Fallback heuristics
    """

    explain = display_field.explain
    field_spec = getattr(display_field, "semantic_field", None)

    # =====================================================
    # ExplainSpec override
    # =====================================================

    if facet == "debug":
        return _build_debug_explanation(
            display_field,
            row_values=row_values,
        )

    if explain is not None:
        value = getattr(explain, facet, None)

        if value:
            # -------------------------------------------------
            # Callable support
            # -------------------------------------------------

            if callable(value):
                return value(
                    display_field=display_field,
                    row_values=row_values,
                )

            return value

    # =====================================================
    # FieldSpec fallback
    # =====================================================

    if field_spec is not None:
        # -------------------------------------------------
        # Variable
        # -------------------------------------------------

        if facet == "variables":
            if field_spec.variable:
                return field_spec.variable

            result = field_spec.name
            return result

        # -------------------------------------------------
        # Sources
        # -------------------------------------------------

        elif facet == "sources":
            result = [field_spec.source]
            return result

        # -------------------------------------------------
        # Units
        # -------------------------------------------------

        elif facet == "units":
            # Future expansion point
            result = facet
            return result

        # -------------------------------------------------
        # Notes
        # -------------------------------------------------

        elif facet == "notes":
            result = facet
            return result

    # =====================================================
    # Final fallback heuristics
    # =====================================================

    if facet == "variables":
        if display_field.description:
            return display_field.description

        return display_field.field_name

    return None


def build_field_explanation(
    display_field: DisplayField,
    explain_facets,
    row_values: list | None = None,
):
    """
    Build explanation text for a display field.
    """

    if not explain_facets:
        return ""

    parts = []

    # =====================================================
    # Variables
    # =====================================================

    if "variables" in explain_facets:
        variable_text = _resolve_explain_facet(
            display_field,
            "variables",
            row_values=row_values,
        )

        if variable_text:
            parts.append(str(variable_text))

    # =====================================================
    # Values
    # =====================================================

    if "values" in explain_facets:
        value_text = _resolve_explain_facet(
            display_field,
            "values",
            row_values=row_values,
        )

        #        if value_text:
        #            parts.append(str(value_text))

        if row_values:
            prefix = "Values:" if len(row_values) > 1 else "Value:"

            parts.append(f"{prefix} {row_values}")
        else:
            parts.append(value_text)

    # =====================================================
    # Sources
    # =====================================================

    if "sources" in explain_facets:
        sources = _resolve_explain_facet(
            display_field,
            "sources",
            row_values=row_values,
        )

        if sources:
            parts.append(f"Sources: {sources}")

    # =====================================================
    # Units
    # =====================================================

    if "units" in explain_facets:
        units_text = _resolve_explain_facet(
            display_field,
            "units",
            row_values=row_values,
        )

        if units_text:
            parts.append(f"Units: {units_text}")

    # =====================================================
    # Notes
    # =====================================================

    if "notes" in explain_facets:
        notes_text = _resolve_explain_facet(
            display_field,
            "notes",
            row_values=row_values,
        )

        if notes_text:
            parts.append(f"Notes: {notes_text}")

    # =====================================================
    # Debug
    # =====================================================

    if "debug" in explain_facets:
        debug_text = _resolve_explain_facet(
            display_field,
            "debug",
            row_values=row_values,
        )

        if debug_text:
            parts.append(debug_text)

    return "\n".join(parts).strip()


# =========================================================
# Raw Field Explanation
# =========================================================


def build_raw_field_explanation(
    field_name,
    explain_facets,
):
    """
    Build explanation text for raw TOML/schema field.

    Used by:
        compare.py

    Unlike build_field_explanation(), this operates
    directly on raw parameter names rather than
    DisplayField definitions.
    """

    if not explain_facets:
        return ""

    generated = get_generated_explain_data(
        field_name,
    )

    if not generated:
        if "debug" in explain_facets:
            return "[missing generated metadata]"

        return ""

    parts = []

    # =====================================================
    # Variables
    # =====================================================

    if "variables" in explain_facets:
        variable = generated.get("variable")

        if variable:
            parts.append(variable)

        elif "debug" in explain_facets:
            parts.append("[missing variable explanation]")

    # =====================================================
    # Values / Units
    # =====================================================

    if "values" in explain_facets:
        units = generated.get("units")

        if units:
            parts.append(f"Units: {units}")

        elif "debug" in explain_facets:
            parts.append("[missing units]")

    # =====================================================
    # Notes
    # =====================================================

    notes = generated.get("notes")

    if notes:
        parts.append(notes)

    # =====================================================
    # Sources
    # =====================================================

    if "sources" in explain_facets:
        section = generated.get("section")

        if section:
            parts.append(f"Section: {section}")

        elif "debug" in explain_facets:
            parts.append("[missing section]")

    return "\n\n".join(parts)
