# src/owlroost/cli/cmd_results.py

from __future__ import annotations

import click

from owlroost.display.bootstrap import build_display_registry
from owlroost.display.dataset import Dataset
from owlroost.display.loaders import load_runs
from owlroost.display.materialize import apply_derived_metrics, materialize_view
from owlroost.display.renderers.latex_table import render_latex_table
from owlroost.display.renderers.markdown_table import render_markdown_table
from owlroost.display.renderers.rich_table import render_rich_table
from owlroost.display.utils import attach_row_ids, inject_id_column
from owlroost.metrics.registry.bootstrap import build_metrics_registry
from owlroost.schema.bootstrap import build_registry

# =========================================================
# Renderer Helpers
# =========================================================


def render_table(
    table,
    renderer,
):
    """
    Dispatch table renderer.
    """

    if renderer == "markdown":
        return render_markdown_table(table)

    if renderer == "latex":
        return render_latex_table(table)

    return render_rich_table(table)


def resolve_renderer(
    markdown=False,
    latex=False,
):
    """
    Resolve renderer name from CLI flags.
    """

    if markdown:
        return "markdown"

    if latex:
        return "latex"

    return "rich"


# =========================================================
# Row Value Resolution
# =========================================================


def resolve_row_value(
    row,
    key,
):
    """
    Resolve value from dataset row.

    Search order:
        _meta
        _metrics
        _inputs (dotted path)
    """

    # -----------------------------------------------------
    # _meta
    # -----------------------------------------------------

    if key in row.get("_meta", {}):
        return row["_meta"][key]

    # -----------------------------------------------------
    # _metrics
    # -----------------------------------------------------

    if key in row.get("_metrics", {}):
        return row["_metrics"][key]

    # -----------------------------------------------------
    # _inputs dotted path
    # -----------------------------------------------------

    current = row.get("_inputs", {})

    for part in key.split("."):
        if not isinstance(current, dict):
            return None

        if part not in current:
            return None

        current = current[part]

    return current


# =========================================================
# Filtering
# =========================================================


def parse_filter_expression(
    expr,
):
    """
    Parse expressions like:

        case_id=0
        trial.completed>50
        success_rate>=0.9
    """

    operators = [
        ">=",
        "<=",
        "!=",
        ">",
        "<",
        "=",
    ]

    for op in operators:
        if op in expr:
            left, right = expr.split(op, 1)

            return (
                left.strip(),
                op,
                right.strip(),
            )

    raise click.ClickException(f"Invalid filter expression: {expr}")


def coerce_value(
    value,
):
    """
    Attempt numeric coercion.
    """

    if value is None:
        return None

    if isinstance(
        value,
        (
            int,
            float,
        ),
    ):
        return value

    s = str(value)

    try:
        if "." in s:
            return float(s)

        return int(s)

    except Exception:
        return s


def compare_values(
    lhs,
    op,
    rhs,
):
    """
    Compare values using operator.
    """

    lhs = coerce_value(lhs)

    rhs = coerce_value(rhs)

    if op == "=":
        return lhs == rhs

    if op == "!=":
        return lhs != rhs

    if op == ">":
        return lhs > rhs

    if op == "<":
        return lhs < rhs

    if op == ">=":
        return lhs >= rhs

    if op == "<=":
        return lhs <= rhs

    raise ValueError(f"Unsupported operator: {op}")


def apply_filters(
    rows,
    filters,
):
    """
    Apply CLI filters.
    """

    if not filters:
        return rows

    out = []

    parsed = [parse_filter_expression(f) for f in filters]

    for row in rows:
        keep = True

        for key, op, rhs in parsed:
            lhs = resolve_row_value(
                row,
                key,
            )

            if not compare_values(lhs, op, rhs):
                keep = False
                break

        if keep:
            out.append(row)

    return out


# =========================================================
# Sorting
# =========================================================


def canonical_sort_key(
    row,
):
    """
    Canonical default ordering.

    Order:
        case_id
        experiment_id
        run_id
        trial_id
    """

    meta = row.get(
        "_meta",
        {},
    )

    case_id = meta.get(
        "case_id",
        -1,
    )

    experiment_id = meta.get(
        "experiment_id",
        "",
    )

    run_id = meta.get(
        "run_id",
        -1,
    )

    trial_id = meta.get(
        "trial_id",
        -1,
    )

    return (
        case_id,
        experiment_id,
        run_id,
        trial_id,
    )


def apply_canonical_sort(
    rows,
):
    """
    Apply canonical hierarchical ordering.

    Order:
        case_id
        experiment_id
        run_id
        trial_id
    """

    return sorted(
        rows,
        key=canonical_sort_key,
    )


def apply_sort(
    rows,
    sort_key,
):
    """
    Sort rows by field.

    Prefix '-' for descending.

    Examples:
        trial.completed
        -trial.completed
    """

    if not sort_key:
        return rows

    descending = False

    key = sort_key

    if sort_key.startswith("-"):
        descending = True
        key = sort_key[1:]

    return sorted(
        rows,
        key=lambda r: (
            resolve_row_value(r, key) is None,
            resolve_row_value(r, key),
        ),
        reverse=descending,
    )


# =========================================================
# Top-N
# =========================================================


def apply_top(
    rows,
    top_n,
):
    """
    Limit rows.
    """

    if top_n is None:
        return rows

    return rows[:top_n]


# =========================================================
# CLI
# =========================================================


@click.command("results")
@click.option(
    "--view",
    default="basic",
    show_default=True,
)
@click.option(
    "--markdown",
    is_flag=True,
)
@click.option(
    "--latex",
    is_flag=True,
)
@click.option(
    "--pivot",
    is_flag=True,
)
@click.option(
    "--filter",
    "filters",
    multiple=True,
    help=("Filter rows. " "Examples: case_id=0 " "trial.completed>50"),
)
@click.option(
    "--sort",
    type=str,
    help=("Sort by field. " "Prefix '-' for descending."),
)
@click.option(
    "--top",
    type=int,
    help="Limit number of rows.",
)
def cmd_results(
    view,
    markdown,
    latex,
    pivot,
    filters,
    sort,
    top,
):
    """
    Display discovered runs from ./results.

    Examples:

      roost results

      roost results --view basic

      roost results --pivot

      roost results --filter case_id=0

      roost results --sort -trial.completed

      roost results --top 10
    """

    # =====================================================
    # Build Registries
    # =====================================================

    schema_registry = build_registry()
    metrics_registry = build_metrics_registry()
    display_registry = build_display_registry(
        schema_registry=schema_registry,
        metrics_registry=metrics_registry,
    )

    # =====================================================
    # Discover + Load Runs
    # =====================================================

    ds = load_runs(
        metrics_registry=metrics_registry,
        results_root="results",
    )

    if not ds.rows:
        click.echo("No runs found.")
        return

    for row in ds.rows:
        apply_derived_metrics(
            row,
            display_registry,
        )

    ds.rows = apply_canonical_sort(
        ds.rows,
    )

    ds = attach_row_ids(ds)

    # =====================================================
    # Working Rows
    # =====================================================

    working_rows = ds.rows

    # =====================================================
    # Filters
    # =====================================================

    working_rows = apply_filters(
        working_rows,
        filters,
    )

    # =====================================================
    # Sort
    # =====================================================

    working_rows = apply_sort(
        working_rows,
        sort,
    )

    # =====================================================
    # Top-N
    # =====================================================

    working_rows = apply_top(
        working_rows,
        top,
    )

    # =====================================================
    # Final Dataset
    # =====================================================

    final_ds = Dataset(
        rows=working_rows,
        level=ds.level,
    )

    # =====================================================
    # Resolve Renderer
    # =====================================================

    renderer = resolve_renderer(
        markdown,
        latex,
    )

    # =====================================================
    # Materialize View
    # =====================================================

    table = materialize_view(
        dataset=final_ds,
        registry=display_registry,
        level="run",
        view_name=view,
        mode="pivot" if pivot else "table",
    )

    # =====================================================
    # Add Row IDs
    # =====================================================

    if not pivot:
        table = inject_id_column(
            table,
            final_ds,
        )

    # =====================================================
    # Render
    # =====================================================

    output = render_table(
        table,
        renderer,
    )

    if output:
        click.echo(output)
