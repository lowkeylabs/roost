# src/owlroost/schema/plugins/group_derived.py

from __future__ import annotations

from collections import defaultdict

from owlroost.display.dataset import Dataset
from owlroost.display.specs import DisplayProfile

from ..registry import FieldSpec

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


def _normalize_overrides(
    overrides,
):
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


def _extract_overrides(
    row,
):
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


def _assign_group_override_metrics(
    rows,
):
    """
    Compute + assign:
        common_overrides
        run_specific_overrides

    across a group of rows.
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
    ds: Dataset,
    *,
    use_working_set=False,
) -> Dataset:
    """
    Apply group-derived analytical metrics.

    Default behavior:
        compute independently per experiment.

    Working-set mode:
        compute across the entire visible dataset.
    """

    rows = ds.rows

    if not rows:
        return ds

    # =====================================================
    # Working-set mode
    # =====================================================

    if use_working_set:
        _assign_group_override_metrics(
            rows,
        )

        return ds

    # =====================================================
    # Experiment-group mode
    # =====================================================

    groups = defaultdict(list)

    for row in rows:
        meta = row.get(
            "_meta",
            {},
        )

        key = (
            meta.get("case_id"),
            meta.get("experiment_id"),
        )

        groups[key].append(row)

    for group_rows in groups.values():
        _assign_group_override_metrics(
            group_rows,
        )

    return ds


# =========================================================
# Plugin
# =========================================================


class GroupDerivedMetricsPlugin:
    """
    Group-derived analytical metrics.

    These metrics:
    - are NOT persisted
    - are computed dynamically
    - depend on groups of rows
    - support experiment comparison analysis
    """

    def register(
        self,
        registry,
    ):
        # =================================================
        # Common Overrides
        # =================================================

        registry.register(
            FieldSpec(
                name="run_execution.common_overrides",
                dtype=list,
                path=(
                    "run_execution",
                    "common_overrides",
                ),
                source="derived",
                level="experiment",
                description=("Overrides shared across " "comparison group."),
                display_profiles={
                    "table": DisplayProfile(
                        label="Common\nOverrides",
                        fmt="overrides",
                        content_align="left",
                        width=40,
                        wrap=True,
                    ),
                    "pivot": DisplayProfile(
                        label="Common Overrides",
                        fmt="overrides",
                        content_align="left",
                        width=40,
                        wrap=True,
                    ),
                },
            )
        )

        # =================================================
        # Run Specific Overrides
        # =================================================

        registry.register(
            FieldSpec(
                name="run_execution.run_specific_overrides",
                dtype=list,
                path=(
                    "run_execution",
                    "run_specific_overrides",
                ),
                source="derived",
                level="experiment",
                description=("Overrides unique within " "comparison group."),
                display_profiles={
                    "table": DisplayProfile(
                        label="Run\nSpecific\nOverrides",
                        fmt="overrides",
                        content_align="left",
                        width=20,
                        wrap=True,
                    ),
                    "pivot": DisplayProfile(
                        label="Run Specific Overrides",
                        fmt="overrides",
                        content_align="left",
                        width=40,
                        wrap=True,
                    ),
                },
            )
        )
