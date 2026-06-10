# src/owlroost/cli/utils.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from pathlib import Path

import click

from owlroost.display.renderers.latex_table import render_latex_table
from owlroost.display.renderers.markdown_table import render_markdown_table
from owlroost.display.renderers.rich_table import render_rich_table

# =========================================================
# Renderer Helpers
# =========================================================

SYSTEM_OVERRIDE_PREFIXES = {
    "session.",
}


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


def select_rows_by_id(
    rows,
    selections,
):
    """
    Return rows matching selected IDs.

    Assumes attach_row_ids() has already
    attached _row_id values.
    """

    if not selections:
        return rows

    wanted = set(
        parse_id_selection(
            selections,
        )
    )

    return [row for row in rows if row.get("_row_id") in wanted]


def split_catalog_args(
    args,
):
    """
    Split catalog CLI args into:

        selectors
        search

    Examples
    --------

        spending
            -> search

        3
            -> selector

        1,3,5
            -> selector

        1-5
            -> selector
    """

    selectors = []
    search_terms = []

    for arg in args:
        if any(c.isdigit() for c in arg) and all(c.isdigit() or c in ",-" for c in arg):
            selectors.append(arg)

        else:
            search_terms.append(arg)

    search = " ".join(search_terms) if search_terms else None

    return selectors, search


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

        roost_settings.trials_per_run=1,10,50
    """

    keys = {
        "roost_settings.trials_per_run",
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


def select_case_rows(
    rows,
    selections,
):
    """
    Return rows matching either:

        0
        1-3
        1,3,5

    or

        case.toml
        ./cases/case.toml
        /full/path/case.toml

    Explicit TOML files bypass catalog
    discovery and are accepted directly.
    """

    if not selections:
        return rows

    selected_rows = []

    for selection in selections:
        path = Path(selection)

        # ----------------------------------------
        # Explicit TOML file selection
        # ----------------------------------------

        if path.exists() and path.is_file() and path.suffix.lower() == ".toml":
            selected_rows.append(
                {
                    "_path": str(
                        path.resolve(),
                    ),
                    "_row_id": None,
                }
            )

            continue

        # ----------------------------------------
        # ID/range selection
        # ----------------------------------------

        matches = select_rows_by_id(
            rows,
            [selection],
        )

        if not matches:
            raise click.ClickException(f"No cases matched selection: {selection}")

        selected_rows.extend(matches)

    # ----------------------------------------
    # Remove duplicates
    # ----------------------------------------

    seen = set()
    out = []

    for row in selected_rows:
        resolved = str(
            Path(
                row["_path"],
            ).resolve()
        )

        if resolved in seen:
            continue

        seen.add(resolved)
        out.append(row)

    return out


def parse_override_request(
    overrides,
    schema_registry,
):
    """
    Validate CLI override requests.

    Notes
    -----
    Schema validation applies only to
    executable schema fields.

    Operational metadata namespaces
    (for example session.*) are exempt.
    """

    errors = []

    for override in overrides:
        if "=" not in override:
            errors.append(f"Invalid override: {override}")
            continue

        field_name, _ = override.split(
            "=",
            1,
        )

        # =========================================
        # Operational overrides
        # =========================================

        if any(
            field_name.startswith(
                prefix,
            )
            for prefix in SYSTEM_OVERRIDE_PREFIXES
        ):
            continue

        # =========================================
        # Schema validation
        # =========================================

        if not schema_registry.exists(
            field_name,
        ):
            errors.append(f"Unknown override field: {field_name}")

    return (
        overrides,
        errors,
    )
