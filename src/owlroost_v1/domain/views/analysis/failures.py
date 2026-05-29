from collections import Counter, defaultdict

from rich import box
from rich.console import Console
from rich.table import Table

from owlroost.domain.formatting import format_value
from owlroost.domain.models.rows import TrialRow
from owlroost.domain.registry import COLUMN_REGISTRY, VIEW_REGISTRY
from owlroost.domain.views.table import build_rows

from ..analysis_registry import register_analysis_view

# =========================================================
# Failure Classification
# =========================================================


def classify_failure(row: TrialRow) -> str:
    """
    Classify a failed trial using solver-provided diagnostics first,
    then fallback to heuristic classification.
    """

    status = (row.status or "").upper()

    # -------------------------------------------------
    # Not a failure
    # -------------------------------------------------
    if status == "SOLVED":
        return "solved"

    if status == "INCOMPLETE":
        return "incomplete"

    # -------------------------------------------------
    # Solver-provided truth (HIGHEST PRIORITY)
    # -------------------------------------------------
    if status == "FAILED":
        if row.failure_detail:
            return row.failure_detail

        if row.failure_category:
            return row.failure_category

        # -------------------------------------------------
        # Fallback heuristics (only if solver gave nothing)
        # -------------------------------------------------

        if row.spend_basis is None and row.total_spend_real is None and row.bequest_real is None:
            return "no_metrics"

        if row.runtime is not None and row.runtime > 10:
            return "slow_failure"

        if row.nvars is not None and row.nvars > 5000:
            return "high_complexity"

        if row.nnz is not None and row.nnz > 100_000:
            return "dense_problem"

        if row.int_ratio is not None and row.int_ratio > 0.2:
            return "integer_heavy"

        if row.spend_basis is not None and row.spend_basis < 1:
            return "spending_collapse"

        if row.bequest_real is not None and row.bequest_real == 0:
            return "zero_bequest"

        if row.total_spend_real is not None and row.total_spend_real < 100_000:
            return "low_spending_plan"

        return "generic_failure"

    return "unknown_failure"


# =========================================================
# Main View
# =========================================================


def view_failures(trial_rows: list[TrialRow]):
    console = Console()

    MAX_EXAMPLES = 5

    # -------------------------------------------------
    # Runtime baseline (median)
    # -------------------------------------------------

    runtimes = [r.runtime for r in trial_rows if r.runtime is not None]

    median_runtime = None
    if runtimes:
        runtimes_sorted = sorted(runtimes)
        median_runtime = runtimes_sorted[len(runtimes_sorted) // 2]

    # -------------------------------------------------
    # Gather data
    # -------------------------------------------------

    counts = Counter()
    examples = defaultdict(list)

    total_trials = len(trial_rows)
    total_failures = 0

    for row in trial_rows:
        category = classify_failure(row)

        # -------------------------------------------------
        # Relative slow override (strong signal)
        # -------------------------------------------------
        if (
            row.status == "FAILED"
            and row.runtime is not None
            and median_runtime is not None
            and row.runtime > 3 * median_runtime
        ):
            category = "slow_failure"

        # -------------------------------------------------
        # Count ONLY actual failures
        # -------------------------------------------------
        if row.status == "FAILED":
            total_failures += 1
            counts[category] += 1

            # store a few examples
            if len(examples[category]) < MAX_EXAMPLES:
                examples[category].append(row)

    # -------------------------------------------------
    # No failures case
    # -------------------------------------------------

    if total_failures == 0:
        console.print("[green]No failures detected.[/green]")
        return

    # -------------------------------------------------
    # Summary table
    # -------------------------------------------------

    table = Table(
        title="Failure Classification",
        header_style="bold red",
        show_edge=False,
    )

    table.add_column("Category", justify="left")
    table.add_column("Count", justify="right")
    table.add_column("% of Failures", justify="right")

    for category, count in counts.most_common():
        pct = count / total_failures if total_failures else 0
        table.add_row(
            category,
            str(count),
            f"{pct:.1%}",
        )

    console.print(table)

    # -------------------------------------------------
    # Summary stats
    # -------------------------------------------------

    console.print()
    console.print(f"Total trials: {total_trials}")
    console.print(f"Failures: {total_failures} ({total_failures / total_trials:.1%})")

    # -------------------------------------------------
    # Build example rows
    # -------------------------------------------------

    example_rows = []

    for category, rows in examples.items():
        for r in rows:
            r.failure_category = category
            example_rows.append(r)

    # -------------------------------------------------
    # Build row dicts via registry
    # -------------------------------------------------

    view_key = "audit_failure_examples"
    column_keys = VIEW_REGISTRY[view_key]

    rows = build_rows(example_rows, column_keys)

    # -------------------------------------------------
    # Render table (same pattern as cmd_audit)
    # -------------------------------------------------

    console.print("\n[bold]Examples[/bold]")

    table = Table(
        header_style="bold cyan",
        row_styles=["none", "none"],
        box=box.SIMPLE,
        show_header=True,
        show_edge=False,
        show_lines=False,
    )

    for key in column_keys:
        col = COLUMN_REGISTRY[key]
        table.add_column(col.label, justify=col.align)

    for row in rows:
        formatted_row = []
        for key in column_keys:
            col = COLUMN_REGISTRY[key]
            formatted = format_value(row[key], col.fmt)
            formatted_row.append(formatted)

        table.add_row(*formatted_row)

    console.print(table)


# =========================================================
# Registration
# =========================================================

register_analysis_view("failures", view_failures)
