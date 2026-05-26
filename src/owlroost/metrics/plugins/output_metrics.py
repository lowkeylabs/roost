# src/owlroost/metrics/registry/plugins/output_metrics.py

from __future__ import annotations

from owlroost.display.specs import (
    DisplayProfile,
)
from owlroost.metrics.specs import (
    MetricFieldSpec,
)


class OutputMetricsPlugin:
    """
    Register canonical output metrics.

    This plugin defines the semantic ontology
    for OwlRoost output metrics.

    MetricsRegistry owns:

        - metric identity
        - semantic meaning
        - compute level
        - aggregation defaults
        - default display semantics

    DisplayRegistry owns:

        - views
        - grouping
        - renderer composition
        - dynamic display behavior
    """

    def register(
        self,
        registry,
    ):
        # =================================================
        # Execution Metrics
        # =================================================

        registry.register(
            MetricFieldSpec(
                name="timing.elapsed_seconds",
                dtype=float,
                compute_level="trial",
                category="execution",
                description=("Elapsed trial execution time " "in seconds."),
                default_aggregates=[
                    "median",
                    "mean",
                    "p10",
                    "p90",
                    "min",
                    "max",
                ],
                profiles={
                    "table": DisplayProfile(
                        label="Elapsed\nSec",
                        fmt="float2",
                        content_align="right",
                    ),
                    "pivot": DisplayProfile(
                        label="Elapsed Seconds",
                        fmt="float2",
                    ),
                },
            )
        )

        # =================================================
        # Trial Completion Metrics
        # =================================================

        registry.register(
            MetricFieldSpec(
                name="trial.completed",
                dtype=int,
                compute_level="run",
                category="execution",
                description=("Completed trial count."),
                profiles={
                    "table": DisplayProfile(
                        label="Done",
                        fmt="int",
                        content_align="right",
                    ),
                    "pivot": DisplayProfile(
                        label="Trials Completed",
                        fmt="int",
                    ),
                },
            )
        )

        registry.register(
            MetricFieldSpec(
                name="trial.pending",
                dtype=int,
                compute_level="run",
                category="execution",
                description=("Pending trial count."),
                profiles={
                    "table": DisplayProfile(
                        label="Pending",
                        fmt="int",
                        content_align="right",
                    ),
                    "pivot": DisplayProfile(
                        label="Trials Pending",
                        fmt="int",
                    ),
                },
            )
        )

        registry.register(
            MetricFieldSpec(
                name="trial.total",
                dtype=int,
                compute_level="run",
                category="execution",
                description=("Total trial count."),
                profiles={
                    "table": DisplayProfile(
                        label="Trials",
                        fmt="int",
                        content_align="right",
                    ),
                    "pivot": DisplayProfile(
                        label="Total Trials",
                        fmt="int",
                    ),
                },
            )
        )

        registry.register(
            MetricFieldSpec(
                name="trial.completion_rate",
                dtype=float,
                compute_level="run",
                category="execution",
                description=("Completed trial fraction."),
                profiles={
                    "table": DisplayProfile(
                        label="Complete\n%",
                        fmt="percent",
                        content_align="right",
                    ),
                    "pivot": DisplayProfile(
                        label="Completion Rate",
                        fmt="percent",
                    ),
                },
            )
        )

        # =================================================
        # Financial Metrics
        # =================================================

        registry.register(
            MetricFieldSpec(
                name="financial.spending.year0.today",
                dtype=float,
                compute_level="trial",
                category="financial",
                description=("Inflation-adjusted spending " "during the first retirement year."),
                default_aggregates=[
                    "median",
                    "p10",
                    "p90",
                ],
                profiles={
                    "table": DisplayProfile(
                        label="Year 0\nSpending",
                        fmt="currency0",
                        content_align="right",
                    ),
                    "pivot": DisplayProfile(
                        label="Year-0 Spending",
                        fmt="currency0",
                    ),
                },
            )
        )

        registry.register(
            MetricFieldSpec(
                name="financial.spending.total.today",
                dtype=float,
                compute_level="trial",
                category="financial",
                description=("Total lifetime spending."),
                default_aggregates=[
                    "median",
                    "p10",
                    "p90",
                ],
                profiles={
                    "table": DisplayProfile(
                        label="Total\nSpend",
                        fmt="currency0",
                        content_align="right",
                    ),
                    "pivot": DisplayProfile(
                        label="Total Spending",
                        fmt="currency0",
                    ),
                },
            )
        )

        registry.register(
            MetricFieldSpec(
                name="financial.bequest.total.today",
                dtype=float,
                compute_level="trial",
                category="financial",
                description=("Terminal bequest value."),
                default_aggregates=[
                    "median",
                    "p10",
                    "p90",
                ],
                profiles={
                    "table": DisplayProfile(
                        label="Bequest",
                        fmt="currency0",
                        content_align="right",
                    ),
                    "pivot": DisplayProfile(
                        label="Terminal Bequest",
                        fmt="currency0",
                    ),
                },
            )
        )
