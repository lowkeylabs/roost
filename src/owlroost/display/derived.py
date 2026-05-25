# src/owlroost/display/derived.py

from __future__ import annotations

# =========================================================
# Derived Metrics
# =========================================================


def apply_derived_metrics(
    row,
    registry,
):
    """
    Materialize derived metrics into row["_metrics"].

    Derived metrics are computed dynamically
    from:
        - inputs
        - metrics
        - metadata

    This step enriches operational rows with
    additional semantic metrics prior to:
        - filtering
        - sorting
        - grouping
        - materialization
        - rendering

    Derived metrics are sourced from the
    schema registry and written into:

        row["_metrics"]

    This function intentionally mutates rows
    in-place.
    """

    metrics = row.setdefault(
        "_metrics",
        {},
    )

    for field in registry.schema_registry.all():
        # =================================================
        # Derived Metrics Only
        # =================================================

        if field.source != "derived":
            continue

        if field.compute_fn is None:
            continue

        # =================================================
        # Compute Metric
        # =================================================

        try:
            value = field.compute_fn(
                row,
            )

        except Exception:
            value = None

        metrics[field.name] = value
