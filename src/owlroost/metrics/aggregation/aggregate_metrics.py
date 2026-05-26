from __future__ import annotations

from dataclasses import replace

from owlroost.display.specs import (
    DisplayField,
    DisplayProfile,
)

# =========================================================
# Aggregate Display Field Registration
# =========================================================


def register_aggregate_display_fields(
    reg,
    metrics_registry,
):
    """
    Auto-register DisplayFields for
    aggregate metric outputs.

    Aggregates are derived from:

        MetricFieldSpec.default_aggregates

    Example
    -------
        financial.bequest.total
            +
        median

        ->
        financial.bequest.total__median

    Notes
    -----
    Aggregate fields are synthetic derived metrics.

    They are intentionally NOT represented
    as hierarchical schema fields.

    Human-curated presentation overrides
    should still live in:

        display/overrides.py

    This system guarantees:
        - field existence
        - validation compatibility
        - materialization support

    The implementation is intentionally
    profile-agnostic.

    Any profile defined on a metric is
    automatically inherited by synthesized
    aggregate fields.
    """

    for metric in metrics_registry.all():
        # =================================================
        # Skip metrics without aggregates
        # =================================================

        if not metric.default_aggregates:
            continue

        # =================================================
        # Source profiles
        # =================================================

        source_profiles = metric.profiles or {}

        for agg_name in metric.default_aggregates:
            agg_field_name = build_aggregate_field_name(
                metric.name,
                agg_name,
            )

            # =================================================
            # Preserve explicit overrides
            # =================================================

            if reg.has_display_field(agg_field_name):
                continue

            # =================================================
            # Build aggregate profiles
            # =================================================

            aggregate_profiles = {}

            for (
                profile_name,
                source_profile,
            ) in source_profiles.items():
                aggregate_profiles[profile_name] = build_aggregate_profile(
                    source_profile=source_profile,
                    agg_name=agg_name,
                    profile_name=profile_name,
                )

            # =================================================
            # Fallback profile generation
            # =================================================

            if not aggregate_profiles:
                aggregate_profiles = {
                    "default": DisplayProfile(
                        label=(f"{metric.name}\n" f"{agg_name.upper()}"),
                    )
                }

            # =================================================
            # Register synthesized display field
            # =================================================

            reg.register_display_field(
                DisplayField(
                    field_name=agg_field_name,
                    description=(f"{agg_name} aggregation " f"for {metric.name}"),
                    profiles=aggregate_profiles,
                )
            )


# =========================================================
# Aggregate Profile Derivation
# =========================================================


def build_aggregate_profile(
    source_profile: DisplayProfile,
    agg_name: str,
    profile_name: str,
):
    """
    Derive aggregate profile from
    source metric profile.

    The profile is cloned while modifying
    only the label.

    Formatting/alignment/wrapping/etc
    are inherited automatically.
    """

    base_label = source_profile.label or ""

    aggregate_label = build_aggregate_label(
        base_label=base_label,
        agg_name=agg_name,
        profile_name=profile_name,
    )

    return replace(
        source_profile,
        label=aggregate_label,
    )


# =========================================================
# Aggregate Label Builder
# =========================================================


def build_aggregate_label(
    base_label: str,
    agg_name: str,
    profile_name: str,
):
    """
    Build aggregate label.

    Different profile types may
    eventually want different
    aggregation label styles.
    """

    # -----------------------------------------------------
    # Table-style labels
    # -----------------------------------------------------

    if profile_name == "table":
        return f"{base_label}\n" f"{agg_name.upper()}"

    # -----------------------------------------------------
    # Default inline style
    # -----------------------------------------------------

    return f"{base_label} " f"{agg_name.upper()}"


# =========================================================
# Helper Utilities
# =========================================================


def build_aggregate_field_name(
    field_name: str,
    agg_name: str,
):
    """
    Construct canonical aggregate field name.

    Example
    -------
        financial.bequest.total
        +
        median

        ->
        financial.bequest.total__median
    """

    return f"{field_name}" f"__{agg_name}"
