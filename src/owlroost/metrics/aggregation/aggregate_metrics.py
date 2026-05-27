# src/owlroost/metrics/aggregation/aggregate_metrics.py

from __future__ import annotations

from dataclasses import (
    replace,
)

from owlroost.display.specs import (
    DisplayField,
    DisplayProfile,
)

from owlroost.metrics.aggregation.registry import (
    AGG_DEFAULT_FMT,
)

# =========================================================
# Helpers
# =========================================================


def normalize_aggregate_definition(
    aggregate,
):
    """
    Normalize aggregate specification.

    Supports:

        "median"

    or:

        ("median", "currency")

    Returns
    -------
    (agg_name, fmt)
    """

    if isinstance(
        aggregate,
        tuple,
    ):
        return aggregate

    return (
        aggregate,
        AGG_DEFAULT_FMT.get(
            aggregate
        ),
    )


# =========================================================
# Aggregate Display Field Registration
# =========================================================


def register_aggregate_display_fields(
    reg,
    metrics_registry,
):
    """
    Register display overlays for aggregate
    analytical projections.

    Notes
    -----
    Aggregate projections are derived from:

        MetricFieldSpec.default_aggregates

    Example
    -------
        timing.elapsed_seconds
            +
        median

        ->
        timing.elapsed_seconds__median

    Architectural Notes
    -------------------
    Aggregate display fields are:

        analytical projection overlays

    layered onto canonical metric ontology.

    They therefore inherit semantic lineage
    from the originating metric specification.

    Human-curated presentation overrides
    still belong in:

        display/overrides.py
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

        source_profiles = (
            metric.profiles or {}
        )

        # =================================================
        # Aggregate Definitions
        # =================================================

        for aggregate in (
            metric.default_aggregates
        ):

            (
                agg_name,
                agg_fmt,
            ) = normalize_aggregate_definition(
                aggregate
            )

            agg_field_name = (
                build_aggregate_field_name(
                    metric.name,
                    agg_name,
                )
            )

            # =================================================
            # Preserve explicit overrides
            # =================================================

            if reg.has_display_field(
                agg_field_name
            ):
                continue

            # =================================================
            # Build aggregate profiles
            # =================================================

            aggregate_profiles = {}

            for (
                profile_name,
                source_profile,
            ) in source_profiles.items():

                aggregate_profiles[
                    profile_name
                ] = build_aggregate_profile(
                    source_profile=(
                        source_profile
                    ),
                    agg_name=agg_name,
                    profile_name=(
                        profile_name
                    ),
                )

            # =================================================
            # Fallback profile generation
            # =================================================

            if not aggregate_profiles:

                aggregate_profiles = {
                    "default": DisplayProfile(
                        label=(
                            f"{metric.name}\n"
                            f"{agg_name.upper()}"
                        ),
                        fmt=agg_fmt,
                    )
                }

            # =================================================
            # Register aggregate overlay
            # =================================================

            reg.register_display_field(
                DisplayField(
                    field_name=(
                        agg_field_name
                    ),
                    path=(
                        f"_metrics."
                        f"{agg_field_name}"
                    ),
                    semantic_field=metric,
                    description=(
                        f"{agg_name} "
                        f"aggregation for "
                        f"{metric.name}"
                    ),
                    profiles=(
                        aggregate_profiles
                    ),
                    default_aggregates=[],
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

    Formatting/alignment/wrapping/etc
    are inherited automatically.
    """

    base_label = (
        source_profile.label or ""
    )

    aggregate_label = (
        build_aggregate_label(
            base_label=base_label,
            agg_name=agg_name,
            profile_name=(
                profile_name
            ),
        )
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
    Build aggregate display label.
    """

    # -----------------------------------------------------
    # Table Labels
    # -----------------------------------------------------

    if profile_name == "table":

        return (
            f"{base_label}\n"
            f"{agg_name.upper()}"
        )

    # -----------------------------------------------------
    # Inline Labels
    # -----------------------------------------------------

    return (
        f"{base_label} "
        f"{agg_name.upper()}"
    )


# =========================================================
# Aggregate Field Naming
# =========================================================


def build_aggregate_field_name(
    field_name: str,
    agg_name: str,
):
    """
    Construct canonical aggregate
    projection field name.

    Example
    -------
        timing.elapsed_seconds
            +
        median

        ->
        timing.elapsed_seconds__median
    """

    return (
        f"{field_name}"
        f"__{agg_name}"
    )
