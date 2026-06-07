# src/owlroost/metrics/plugins/hydra_overrides.py
#
# Copyright (c) 2026 John Leonard
# All rights reserved.
# SPDX-License-Identifier: LicenseRef-OwlRoost-Proprietary
# See LICENSE file in repository root.

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from collections import defaultdict

from ..registry import MetricSpec

# =========================================================
# Override filtering
# =========================================================

EXCLUDED_OVERRIDE_PREFIXES = {
    "case.file",
    "case.name",
}

# =========================================================
# Helpers
# =========================================================


def _normalize_overrides(overrides):
    """
    Normalize overrides into a clean dictionary.

    Example:

        solver_options.solver=HiGHS

    becomes:

        {
            "solver_options.solver": "HiGHS"
        }
    """

    if not overrides:
        return {}

    normalized = {}

    for x in overrides:
        x = str(x).strip()

        if not x:
            continue

        if "=" not in x:
            continue

        key, value = x.split(
            "=",
            1,
        )

        key = key.strip()
        value = value.strip()

        if key in EXCLUDED_OVERRIDE_PREFIXES:
            continue

        normalized[key] = value

    return normalized


def _extract_overrides(row):
    """
    Extract Hydra overrides from row metadata.
    """

    meta = row.get(
        "_meta",
        {},
    )

    overrides = meta.get(
        "task_overrides",
        [],
    )

    return _normalize_overrides(
        overrides,
    )


def _assign_group_override_metrics(rows):
    """
    Compute + assign:

        - common_overrides
        - run_specific_overrides

    across a comparison group.
    """

    if not rows:
        return

    override_sets = [_extract_overrides(row) for row in rows]

    # =====================================================
    # Common overrides
    # =====================================================

    common_items = set.intersection(*[set(d.items()) for d in override_sets])

    common = dict(common_items)

    # =====================================================
    # Per-row specifics
    # =====================================================

    for row, override_set in zip(
        rows,
        override_sets,
        strict=False,
    ):
        specific = {k: v for k, v in override_set.items() if common.get(k) != v}

        metrics = row.setdefault(
            "_metrics",
            {},
        )

        metrics["run_execution.common_overrides"] = common

        metrics["run_execution.run_specific_overrides"] = specific


# =========================================================
# Public API
# =========================================================


def apply_group_derived_metrics(
    dataset,
    *,
    use_working_set=False,
):
    """
    Apply group-derived analytical metrics.

    Default behavior:
        compute independently per session.

    Working-set mode:
        compute across the entire visible
        dataset.
    """

    rows = dataset.rows

    if not rows:
        return dataset

    # =====================================================
    # Working-set mode
    # =====================================================

    if use_working_set:
        _assign_group_override_metrics(
            rows,
        )

        return dataset

    # =====================================================
    # Session-group mode
    # =====================================================

    groups = defaultdict(list)

    for row in rows:
        meta = row.get(
            "_meta",
            {},
        )

        key = (
            meta.get("case_id"),
            meta.get("session_id"),
        )

        groups[key].append(row)

    for group_rows in groups.values():
        _assign_group_override_metrics(
            group_rows,
        )

    return dataset


# =========================================================
# Plugin
# =========================================================


class HydraOverridesPlugin:
    """
    Comparative analytical metrics derived
    from Hydra override structure.

    These metrics are:

        - NOT persisted
        - computed dynamically
        - depend on comparison groups
        - support multirun comparison
        - support explainability workflows
        - support sweep interpretation

    These metrics intentionally model:

        comparative analytical semantics

    rather than direct runtime
    observations.
    """

    def register(
        self,
        registry,
    ):
        # =================================================
        # Common Overrides
        # =================================================

        registry.register(
            MetricSpec(
                # =========================================
                # Identity
                # =========================================
                name=("run_execution.common_overrides"),
                category="derived_metric",
                description=("Overrides shared across comparison group."),
                # =========================================
                # Provenance
                # =========================================
                defined_in=__name__,
                derived_from=[
                    "_meta.task_overrides",
                ],
                # =========================================
                # Typing
                # =========================================
                dtype=dict,
                # =========================================
                # Ontology
                # =========================================
                owner="ROOST",
                semantic_domain="design",
                value_origin="roost-computed",
                projection_kind="synthetic",
                analytic_kind="comparative",
                materialization_level="session",
                # =========================================
                # Materialization
                # =========================================
                compute_fn=None,
                # =========================================
                # Aggregation
                # =========================================
                aggregatable=False,
                default_aggregates=[],
                aggregate_function=None,
                # =========================================
                # Notes
                # =========================================
                notes=(
                    "Computed dynamically from "
                    "Hydra task overrides visible "
                    "within a comparison group."
                ),
            )
        )

        # =================================================
        # Run-Specific Overrides
        # =================================================

        registry.register(
            MetricSpec(
                # =========================================
                # Identity
                # =========================================
                name=("run_execution.run_specific_overrides"),
                category="derived_metric",
                description=("Overrides unique within comparison group."),
                # =========================================
                # Provenance
                # =========================================
                defined_in=__name__,
                derived_from=[
                    "_meta.task_overrides",
                ],
                # =========================================
                # Typing
                # =========================================
                dtype=dict,
                # =========================================
                # Ontology
                # =========================================
                owner="ROOST",
                semantic_domain="design",
                value_origin="roost-computed",
                projection_kind="synthetic",
                analytic_kind="comparative",
                materialization_level="session",
                # =========================================
                # Materialization
                # =========================================
                compute_fn=None,
                # =========================================
                # Aggregation
                # =========================================
                aggregatable=False,
                default_aggregates=[],
                aggregate_function=None,
                # =========================================
                # Notes
                # =========================================
                notes=(
                    "Computed dynamically from "
                    "Hydra task overrides visible "
                    "within a comparison group."
                ),
            )
        )
