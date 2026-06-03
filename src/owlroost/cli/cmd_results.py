# src/owlroost/cli/cmd_results.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

import click

from owlroost.catalog.comparison.supersession import (
    collect_superseded_rows,
    find_superseded_rows,
)
from owlroost.catalog.loaders import load_catalog_rows
from owlroost.cli.utils import (
    parse_id_selection,
    render_table,
    resolve_renderer,
    select_rows_by_id,
    split_build_args,
)
from owlroost.display.bootstrap import build_display_registry
from owlroost.display.explain import (
    VALID_EXPLAIN_FACETS,
    normalize_explain_facets,
)
from owlroost.display.loaders import load_run_rows
from owlroost.display.materializers.compare import materialize_compare_table
from owlroost.display.materializers.materialize import materialize_view
from owlroost.display.operations.filtering import apply_filters
from owlroost.display.operations.help import render_field_help
from owlroost.display.operations.row_ops import apply_top, attach_row_ids
from owlroost.display.operations.sorting import apply_canonical_sort, apply_sort
from owlroost.display.operations.table_ops import inject_id_column
from owlroost.display.projection import project_rows
from owlroost.metrics.bootstrap import build_metrics_registry
from owlroost.operations.delete import collect_delete_targets, delete_paths
from owlroost.operations.promote import collect_promote_targets, promote_runs
from owlroost.schema.bootstrap import build_schema_registry

# =========================================================
# Helpers
# =========================================================


def build_filter_examples(
    level,
):
    """
    Context-sensitive filter examples.
    """

    if level == "session":
        return [
            "--filter run.count>5",
            "--filter trial.total>100",
            "--filter session.date=2026-05-22",
        ]

    if level == "case":
        return [
            "--filter session.count>2",
            "--filter run.count>10",
            "--filter trial.total>500",
        ]

    return [
        "--filter id=in:1,2,3",
        "--filter trial.completed>50",
        "--filter metrics.success_rate>0.9",
        "--filter status=success",
    ]


def build_sort_examples(
    level,
):
    """
    Context-sensitive sort examples.
    """

    if level == "session":
        return [
            "--sort run.count",
            "--sort -trial.total",
            "--sort session.date",
        ]

    if level == "case":
        return [
            "--sort session.count",
            "--sort -run.count",
            "--sort -trial.total",
        ]

    return [
        "--sort throughput",
        "--sort -throughput",
        "--sort elapsed",
    ]


# =========================================================
# CLI
# =========================================================


@click.command("results")
@click.argument(
    "args",
    nargs=-1,
)
@click.option(
    "--view",
    default="results",
    show_default=True,
)
@click.option(
    "--level",
    type=click.Choice(
        ["case", "session", "run", "trial"],
        case_sensitive=False,
    ),
    default="run",
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
    help="Render transposed pivot layout.",
)
@click.option(
    "--compare",
    is_flag=True,
    help="Structural side-by-side comparison.",
)
@click.option(
    "--diff",
    is_flag=True,
    help="Show only differing structural fields.",
)
@click.option(
    "--explain",
    type=str,
    help=("Explanation facets. Comma-separated list from: variables,values,sources,debug,all"),
)
@click.option(
    "--delete",
    "delete_selection",
    type=str,
    help=("Delete rows by displayed row IDs. Examples: 1,2,5-8"),
)
@click.option(
    "--promote",
    "promote_selection",
    type=str,
    help=("Promote runs by displayed row IDs. Examples: 1,2,5-8"),
)
@click.option(
    "--purge",
    is_flag=True,
    help=("Delete older superseded equivalent runs."),
)
@click.option(
    "--filter",
    "filters",
    multiple=True,
    help=("Filter rows. Examples: trial.completed>50 metrics.success_rate>0.9"),
)
@click.option(
    "--sort",
    type=str,
    help="Sort by field. Prefix '-' for descending.",
)
@click.option(
    "--top",
    type=int,
    help="Limit number of rows.",
)
def cmd_results(
    args,
    view,
    level,
    markdown,
    latex,
    pivot,
    compare,
    diff,
    explain,
    delete_selection,
    promote_selection,
    purge,
    filters,
    sort,
    top,
):
    """
    Display discovered results from the operational tree.

    Examples:

      roost results

      roost results 0

      roost results 0,1,2

      roost results --view basic

      roost results --pivot

      roost results --compare

      roost results --diff

      roost results --filter case_id=0

      roost results --sort -trial.completed

      roost results --top 10

      roost results 0 --explain=all
    """

    # =====================================================
    # Validate unsupported combinations
    # =====================================================

    if level == "trial":
        raise click.ClickException("Trial-level projection is not yet implemented.")

    if purge and level != "run":
        raise click.ClickException("--purge only supported at run level.")

    if purge and delete_selection:
        raise click.ClickException("--purge and --delete cannot be combined.")

    if purge and (compare or diff or pivot):
        raise click.ClickException("--purge is not compatible with --compare/--diff/--pivot.")

    if (compare or diff) and level not in {
        "case",
        "run",
    }:
        raise click.ClickException("--compare/--diff only supported for case and run levels.")

    if promote_selection and pivot:
        raise click.ClickException("--promote is not supported with --pivot.")

    if promote_selection and (compare or diff):
        raise click.ClickException("--promote is not supported with --compare/--diff.")

    if promote_selection and level != "run":
        raise click.ClickException("--promote only supported at run level.")

    if explain:
        requested = {x.strip() for x in explain.split(",") if x.strip()}

        invalid = requested - VALID_EXPLAIN_FACETS

        if invalid:
            raise click.BadParameter(f"Unknown explain facet(s): {', '.join(sorted(invalid))}")

    explain_facets = normalize_explain_facets(
        explain,
    )

    # =====================================================
    # Parse CLI args
    # =====================================================

    selectors, overrides = split_build_args(
        args,
    )

    if overrides:
        raise click.ClickException("Hydra-style overrides are not supported in 'roost results'.")

    # =====================================================
    # Build Registries
    # =====================================================

    schema_registry = build_schema_registry()
    metrics_registry = build_metrics_registry()
    display_registry = build_display_registry(
        schema_registry=schema_registry,
        metrics_registry=metrics_registry,
    )
    catalog_rows = load_catalog_rows(
        schema_registry=schema_registry,
        metrics_registry=metrics_registry,
        display_registry=display_registry,
    )
    catalog_index = {row["field_name"]: row for row in catalog_rows}

    # =====================================================
    # Discover + Load Runs
    # =====================================================

    rows = load_run_rows(
        metrics_registry=metrics_registry,
        results_root="results",
    )

    # =====================================================
    # No Results
    # =====================================================

    if not rows:
        click.echo("No runs found.")
        return

    # =====================================================
    # Derived Metrics
    # =====================================================

    #    for row in rows:
    #        apply_derived_metrics(
    #            row,
    #            display_registry,#
    #         )

    # =====================================================
    # Project rows
    # =====================================================

    rows = project_rows(
        rows,
        level=level,
    )

    rows = attach_row_ids(
        rows,
    )

    # =====================================================
    # Context-sensitive CLI help
    # =====================================================

    if "help" in (filters or ()):
        render_field_help(
            rows=rows,
            registry=display_registry,
            level=level,
            view_name=view,
            mode="view",
            title="Available filter fields",
            examples=build_filter_examples(
                level,
            ),
        )

        return

    if "help-all" in (filters or ()):
        render_field_help(
            rows=rows,
            registry=display_registry,
            level=level,
            view_name=view,
            mode="all",
            title="All queryable fields",
        )

        return

    if sort == "help":
        render_field_help(
            rows=rows,
            registry=display_registry,
            level=level,
            view_name=view,
            mode="view",
            title="Available sort fields",
            examples=build_sort_examples(
                level,
            ),
        )

        return

    if sort == "help-all":
        render_field_help(
            rows=rows,
            registry=display_registry,
            level=level,
            view_name=view,
            mode="all",
            title="All queryable fields",
            examples=build_sort_examples(
                level,
            ),
        )

        return

    if str(top).lower() == "help":
        click.echo()
        click.echo("Limit displayed rows.")
        click.echo()
        click.echo("Examples:")
        click.echo()
        click.echo("  --top 5")
        click.echo("  --top 10")
        click.echo()

        return

    # =====================================================
    # Dataset Pipeline
    # =====================================================

    rows = apply_canonical_sort(
        rows,
    )

    rows = apply_filters(
        rows,
        filters,
    )

    rows = apply_sort(
        rows,
        sort,
    )

    rows = apply_top(
        rows,
        top,
    )

    rows = attach_row_ids(
        rows,
    )

    if selectors:
        rows = select_rows_by_id(
            rows,
            selectors,
        )

    # =====================================================
    # Detect superseded runs
    # =====================================================

    if level == "run":
        find_superseded_rows(
            rows,
        )

    # =====================================================
    # No Matching Results
    # =====================================================

    if not rows:
        click.echo(f"No matching {level}s found.")
        return

    # =====================================================
    # Resolve Renderer
    # =====================================================

    renderer = resolve_renderer(
        markdown,
        latex,
    )

    # =====================================================
    # Purge Superseded Runs
    # =====================================================

    if purge:
        superseded_rows = collect_superseded_rows(
            rows,
        )

        if not superseded_rows:
            click.echo()

            click.echo("No superseded runs found.")

            click.echo()

            return

        purge_table = materialize_view(
            rows=superseded_rows,
            registry=display_registry,
            catalog_index=catalog_index,
            level=level,
            view_name=view,
            mode="table",
            explain=explain_facets,
        )

        purge_table = inject_id_column(
            purge_table,
            superseded_rows,
        )

        click.echo()

        click.echo("The following superseded run(s) will be permanently deleted:")

        click.echo()

        preview = render_table(
            purge_table,
            renderer,
        )

        click.echo()

        confirmed = click.confirm(
            "Proceed",
            default=False,
        )

        if not confirmed:
            click.echo("Purge cancelled.")

            return

        targets = collect_delete_targets(
            superseded_rows,
            "run",
        )

        deleted = delete_paths(
            targets,
        )

        click.echo()

        for path in deleted:
            click.echo(f"Deleted: {path}")

        click.echo()

        click.echo(f"Purged {len(deleted)} run(s).")

        return

    # =====================================================
    # Delete
    # =====================================================

    if delete_selection:
        if pivot:
            raise click.ClickException("--delete is not supported with --pivot.")

        if compare or diff:
            raise click.ClickException("--delete is not supported with --compare/--diff.")

        if level == "trial":
            raise click.ClickException("Trial deletion is not supported.")

        selected_ids = parse_id_selection(
            [delete_selection],
        )

        rows_to_delete = select_rows_by_id(
            rows,
            selected_ids,
        )

        if not rows_to_delete:
            raise click.ClickException("No matching row IDs selected.")

        delete_table = materialize_view(
            rows=rows_to_delete,
            registry=display_registry,
            catalog_index=catalog_index,
            level=level,
            view_name=view,
            mode="table",
            explain=explain_facets,
        )

        delete_table = inject_id_column(
            delete_table,
            rows_to_delete,
        )

        click.echo()

        click.echo(f"The following {level}(s) will be permanently deleted:")

        click.echo()

        preview = render_table(
            delete_table,
            renderer,
        )

        click.echo()

        confirmed = click.confirm(
            "Proceed",
            default=False,
        )

        if not confirmed:
            click.echo("Delete cancelled.")
            return

        targets = collect_delete_targets(
            rows_to_delete,
            level,
        )

        deleted = delete_paths(
            targets,
        )

        click.echo()

        for path in deleted:
            click.echo(f"Deleted: {path}")

        click.echo()

        click.echo(f"Deleted {len(deleted)} item(s).")

        return

    # =====================================================
    # Promote
    # =====================================================

    if promote_selection:
        selected_ids = parse_id_selection(
            [promote_selection],
        )

        rows_to_promote = select_rows_by_id(
            rows,
            selected_ids,
        )

        if not rows_to_promote:
            raise click.ClickException("No matching row IDs selected.")

        promote_table = materialize_view(
            rows=rows_to_promote,
            registry=display_registry,
            catalog_index=catalog_index,
            level=level,
            view_name=view,
            mode="table",
            explain=explain_facets,
        )

        promote_table = inject_id_column(
            promote_table,
            rows_to_promote,
        )

        preview = render_table(
            promote_table,
            renderer,
        )

        click.echo()

        click.echo("The following run(s) will be promoted:")

        click.echo()

        if preview:
            click.echo(preview)

        click.echo()

        confirmed = click.confirm(
            "Proceed",
            default=False,
        )

        if not confirmed:
            click.echo("Promotion cancelled.")
            return

        targets = collect_promote_targets(
            rows_to_promote,
        )

        promoted = promote_runs(
            targets,
            cwd=".",
        )

        click.echo()

        empty_diff_count = 0

        for item in promoted:
            path = item["path"]

            diff_is_empty = item.get(
                "diff_is_empty",
                False,
            )

            click.echo(f"Promoted: {path}")

            if diff_is_empty:
                empty_diff_count += 1

        click.echo()

        if empty_diff_count:
            click.echo(
                "Warning: "
                f"{empty_diff_count} promoted run(s) "
                "had no semantic differences from "
                "their parent TOML."
            )

            click.echo()

        click.echo(f"Promoted {len(promoted)} run(s).")

        return

    # =====================================================
    # Structural compare/diff mode
    # =====================================================

    if compare or diff:
        table = materialize_compare_table(
            rows=rows,
            diff_only=diff,
            explain=explain_facets,
        )

        output = render_table(
            table,
            renderer,
        )

        if output:
            click.echo(
                output,
            )

        return

    # =====================================================
    # Materialize View
    # =====================================================

    table = materialize_view(
        rows=rows,
        registry=display_registry,
        catalog_index=catalog_index,
        level=level,
        view_name=view,
        mode="pivot" if pivot else "table",
        explain=explain_facets,
    )

    # =====================================================
    # Add Row IDs
    # =====================================================

    if not pivot:
        table = inject_id_column(
            table,
            rows,
        )

    # =====================================================
    # Render
    # =====================================================

    output = render_table(
        table,
        renderer,
    )

    if output:
        click.echo(
            output,
        )
