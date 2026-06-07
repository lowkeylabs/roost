# src/owlroost/cli/cmd_reports.py
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

from owlroost.reports.reports import (
    collect_report_diagnostics,
    initialize_templates,
    sync_reports,
)


# =========================================================
# CLI
# =========================================================
@click.command("reports")
@click.option(
    "--init",
    "init_src",
    type=click.Path(path_type=Path),
    help="Initialize templates from source folder.",
)
@click.option(
    "--sync",
    is_flag=True,
    help="Sync reporting artifacts.",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing ./templates folder.",
)
@click.option(
    "--results-dir",
    type=click.Path(path_type=Path),
    default=Path("./results"),
)
@click.option(
    "--templates-dir",
    type=click.Path(path_type=Path),
    default=Path("./templates"),
)
def cmd_reports(
    init_src,
    sync,
    force,
    results_dir: Path,
    templates_dir: Path,
):
    """
    Manage reporting layer.

    Modes:
      --init <path> : initialize templates
      --sync        : generate report artifacts
      (none)        : diagnostics
    """

    results_dir = Path(results_dir).resolve()

    templates_dir = Path(templates_dir).resolve()

    # =====================================================
    # INIT
    # =====================================================
    if init_src is not None:
        try:
            result = initialize_templates(
                source_dir=init_src,
                destination_dir=templates_dir,
                project_root=Path.cwd(),
                force=force,
            )

        except Exception as exc:
            raise click.ClickException(str(exc)) from exc

        click.echo(f"Templates initialized: {result['templates_dir']}")

        moved = result["moved_files"]

        if moved:
            click.echo()

            for fname in moved:
                click.echo(f"Moved {fname} → project root")

        return

    # =====================================================
    # SYNC
    # =====================================================
    if sync:
        if not results_dir.exists():
            raise click.ClickException(f"Results directory not found: {results_dir}")

        if not templates_dir.exists():
            raise click.ClickException(f"Templates directory not found: {templates_dir}")

        try:
            sync_reports(
                results_dir,
                templates_dir,
            )

        except Exception as exc:
            raise click.ClickException(str(exc)) from exc

        click.echo("Report sync complete.")

        return

    # =====================================================
    # DIAGNOSTICS
    # =====================================================
    if not results_dir.exists():
        raise click.ClickException(f"Results directory not found: {results_dir}")

    diagnostics = collect_report_diagnostics(
        results_dir,
        templates_dir,
    )

    template_status = diagnostics["template_status"]

    counts = diagnostics["counts"]

    # =====================================================
    # Render diagnostics
    # =====================================================
    click.echo("Reporting Diagnostics\n")

    # ----------------------------------------
    # Template status
    # ----------------------------------------
    if not template_status["exists"]:
        click.echo("Templates:   MISSING (./templates not found)")

    elif template_status["missing_subdirs"]:
        missing = ", ".join(template_status["missing_subdirs"])

        click.echo(f"Templates:   INCOMPLETE (missing: {missing})")

    else:
        click.echo("Templates:   OK")

    click.echo()

    # ----------------------------------------
    # Counts
    # ----------------------------------------
    def line(label, key):
        c = counts[key]

        click.echo(f"{label:<12} {c['total']:>6} (missing: {c['missing']})")

    line("Cases:", "case")
    line("Sessions:", "session")
    line("Runs:", "run")
    line("Trials:", "trial")

    click.echo()

    # ----------------------------------------
    # Final status
    # ----------------------------------------
    if diagnostics["healthy"]:
        click.echo("✔ Reporting system is fully in sync.")

    else:
        click.echo("⚠ Reporting system is NOT in sync.")
