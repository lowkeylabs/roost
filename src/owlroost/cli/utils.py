# src/owlroost/cli/utils.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

import click

from owlroost.display.renderers.latex_table import render_latex_table
from owlroost.display.renderers.markdown_table import render_markdown_table
from owlroost.display.renderers.rich_table import render_rich_table
from owlroost.display.utils import attach_row_ids

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


def parse_id_selection(
    values,
):
    """
    Parse CLI ID selections.

    Supports:
        0
        1,2,3
        0-5
        0,1,3-5,10-12,13

    Returns:
        sorted list[int]
    """

    if not values:
        return []

    selected = set()

    for value in values:
        # Allow:
        #   ("0,1,2",)
        #   ("0", "1", "2")
        parts = str(value).split(",")

        for part in parts:
            part = part.strip()

            if not part:
                continue

            # ----------------------------------------
            # Range
            # ----------------------------------------
            if "-" in part:
                try:
                    start_s, end_s = part.split("-", 1)

                    start = int(start_s)
                    end = int(end_s)

                except ValueError as exc:
                    raise click.ClickException(f"Invalid range selection: {part}") from exc

                if end < start:
                    raise click.ClickException(f"Invalid descending range: {part}")

                for i in range(start, end + 1):
                    selected.add(i)

            # ----------------------------------------
            # Single value
            # ----------------------------------------
            else:
                try:
                    selected.add(int(part))

                except ValueError as exc:
                    raise click.ClickException(f"Invalid selection: {part}") from exc

    return sorted(selected)


def select_dataset_rows(
    dataset,
    selections,
):
    """
    Return dataset rows matching parsed selections.

    Assumes attach_row_ids() has already run.
    """

    if not selections:
        return dataset.rows

    wanted = {int(x) for x in selections}

    selected_rows = []

    for row in dataset.rows:
        row_id = row.get("_row_id")

        if row_id in wanted:
            selected_rows.append(row)

    return selected_rows


def prepare_dataset(
    ds,
    selectors=None,
    filters=None,
    sort=None,
    top=None,
):
    ds = ds.canonical_sort()

    ds = attach_row_ids(ds)

    selected_ids = parse_id_selection(selectors)

    if selected_ids:
        ds.rows = select_dataset_rows(
            ds,
            selected_ids,
        )

    ds = ds.filter(*(filters or []))

    ds = ds.sort(sort)

    ds = ds.top(top)

    return ds


def split_build_args(
    args,
):
    """
    Split mixed CLI args into:

    - selectors
    - hydra overrides

    Selector examples:
        0
        0,1-3,7

    Override examples:
        solver_options.bequest=0
        rates_selection.method=bootstrap_sor
    """

    selectors = []
    overrides = []

    for arg in args:
        if "=" in arg:
            overrides.append(arg)

        else:
            selectors.append(arg)

    return selectors, overrides


def overrides_request_trials(
    overrides,
):
    """
    Return True if overrides specify
    trials_per_run > 0.

    Supports Hydra sweep syntax like:

        roost_runtime.trials_per_run=1,10,50
    """

    keys = {
        "roost_runtime.trials_per_run",
        "roost.trials_per_run",
        "runtime.trials_per_run",
    }

    for override in overrides:
        if "=" not in override:
            continue

        key, value = override.split("=", 1)

        key = key.strip()
        value = value.strip()

        if key not in keys:
            continue

        # ----------------------------------------
        # Hydra sweep values
        # ----------------------------------------

        for token in value.split(","):
            token = token.strip()

            if not token:
                continue

            try:
                if int(token) > 0:
                    return True

            except ValueError:
                # Ignore non-integer sweep tokens
                pass

    return False
