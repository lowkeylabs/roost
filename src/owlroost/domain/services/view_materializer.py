# src/owlroost/domain/services/view_materializer.py

from owlroost.domain.metrics.metric_spec import (
    build_visibility_context,
    resolve_metric_value,
)
from owlroost.domain.models.table import RoostTable


# =========================================================
# Shared value resolver
# =========================================================
def get_value(row, rm, ctx=None):
    val, fmt_override = resolve_metric_value(row, rm.key, getattr(rm, "aggregate", None))

    formatted = rm.spec.render_value(val, row=row, ctx=ctx, fmt_override=fmt_override)

    return {
        "value": val,
        "formatted": formatted,
    }


def _get_separator_label(rm):
    # dict-style (your current view definitions)
    if isinstance(rm, dict):
        return rm.get("label", "") or ""

    # object-style (future-proof)
    if hasattr(rm, "label"):
        return rm.label or ""

    return ""


def _is_separator(rm):
    return isinstance(rm, dict) and "separator" in rm


# =========================================================
# Main dispatcher
# =========================================================
def materialize_view(rows, view, layout="table", explain=None):
    if isinstance(rows, dict):
        rows = [rows]

    if not rows:
        return RoostTable(columns=[], rows=[], layout=layout, meta={"rms": []})

    ctx = build_visibility_context(rows)

    def _view_allows(show_if, layout):
        if show_if is None:
            return True
        if show_if == "is_pivot":
            return layout == "pivot"
        if show_if == "is_table":
            return layout == "table"
        return True

    def _get_label(rm):
        return (rm.spec.label or rm.key).strip()

    def _get_label_with_agg(rm):
        label = _get_label(rm)
        agg = getattr(rm, "aggregate", None)

        if agg and ctx["is_stochastic"]:
            label = f"{label}\n({agg})"

        return label

    # ----------------------------------------
    # Filter view (KEEP separators)
    # ----------------------------------------
    filtered_view = []

    for rm in view:
        if getattr(rm, "spec", None) is None:
            filtered_view.append(rm)
            continue

        if rm.view_show_if and not _view_allows(rm.view_show_if, layout):
            continue

        filtered_view.append(rm)

    # ----------------------------------------
    # Deduplicate (metrics only)
    # ----------------------------------------
    if ctx["is_single"]:
        seen = set()
        deduped = []

        for rm in filtered_view:
            if getattr(rm, "spec", None) is None:
                deduped.append(rm)
                continue

            if rm.key in seen:
                continue

            seen.add(rm.key)
            deduped.append(rm)

        filtered_view = deduped

    # ----------------------------------------
    # Extract metrics only (for table layout)
    # ----------------------------------------
    metric_rms = [rm for rm in filtered_view if getattr(rm, "spec", None)]

    # =========================================================
    # TABLE
    # =========================================================
    if layout == "table":
        labels = [_get_label_with_agg(rm) for rm in metric_rms]

        columns = ["ID", "run_label"] + labels
        rows_out = []

        for i, row in enumerate(rows):
            label = row.get("run_label") or f"row_{i}"

            row_values = [i, label]

            for rm in metric_rms:
                row_values.append(get_value(row, rm, ctx))

            rows_out.append(row_values)

        return RoostTable(
            columns,
            rows_out,
            layout="table",
            meta={
                "rms": metric_rms,
                "layout": layout,
                "align": {
                    (rm.key, getattr(rm, "aggregate", None)): rm.spec.align or "right"
                    for rm in metric_rms
                },
                "wrap": {
                    (rm.key, getattr(rm, "aggregate", None)): rm.spec.wrap
                    for rm in metric_rms
                    if getattr(rm.spec, "wrap", None)
                },
                "column_keys": ["ID", "run_label"]
                + [(rm.key, getattr(rm, "aggregate", None)) for rm in metric_rms],
                "context": ctx,
                "explain": explain,
                "value_mode": "dual",
                "level": "unknown",
                "group_key": "run_label",
            },
        )

    # =========================================================
    # PIVOT (FIXED: includes separators)
    # =========================================================
    if layout == "pivot":
        columns = ["Metric"] + [str(i) for i in range(len(rows))]

        rows_out = []
        row_keys = []
        rms_out = []

        for rm in filtered_view:
            # ----------------------------------------
            # Separator
            # ----------------------------------------
            if getattr(rm, "spec", None) is None:
                label = _get_separator_label(rm)

                rows_out.append([label] + [""] * len(rows))
                row_keys.append(None)
                rms_out.append(rm)
                continue
            # ----------------------------------------
            # Metric
            # ----------------------------------------
            label = _get_label_with_agg(rm)
            key = (rm.key, getattr(rm, "aggregate", None))

            row_cells = [label]

            for r in rows:
                row_cells.append(get_value(r, rm, ctx))

            rows_out.append(row_cells)
            row_keys.append(key)
            rms_out.append(rm)

        return RoostTable(
            columns,
            rows_out,
            layout="pivot",
            meta={
                "rms": rms_out,
                "layout": layout,
                # ----------------------------------------
                # Column-based
                # ----------------------------------------
                "align": {
                    (rm.key, getattr(rm, "aggregate", None)): rm.spec.align or "right"
                    for rm in metric_rms
                },
                "wrap": {
                    (rm.key, getattr(rm, "aggregate", None)): rm.spec.wrap
                    for rm in metric_rms
                    if getattr(rm.spec, "wrap", None)
                },
                # ----------------------------------------
                # Row-based (aligned with rows_out)
                # ----------------------------------------
                "row_keys": row_keys,
                "row_wrap": {
                    key: rm.spec.wrap
                    for key, rm in zip(row_keys, rms_out, strict=False)
                    if key and getattr(rm, "spec", None) and getattr(rm.spec, "wrap", None)
                },
                # ----------------------------------------
                # Existing
                # ----------------------------------------
                "rows": rows,
                "context": ctx,
                "explain": explain,
                "value_mode": "dual",
                "level": "unknown",
                "group_key": "run_label",
            },
        )
