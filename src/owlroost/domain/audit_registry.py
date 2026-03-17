from .registry import Column, register_column, register_view

# =========================================================
# COLUMNS
# =========================================================

register_column(
    Column(
        key="id",
        label="ID",
        extractor=lambda r: r.id,
        group="audit",
        align="right",
    )
)

register_column(
    Column(
        key="case",
        label="Case",
        extractor=lambda r: r.case,
        group="audit",
        align="left",
    )
)

register_column(
    Column(
        key="date",
        label="Date",
        extractor=lambda r: r.date,
        group="audit",
        align="left",
    )
)

register_column(
    Column(
        key="time",
        label="Time",
        extractor=lambda r: r.time,
        group="audit",
        align="left",
    )
)

register_column(
    Column(
        key="runs",
        label="Runs",
        extractor=lambda r: r.runs,
        group="audit",
        align="right",
    )
)

register_column(
    Column(
        key="trials",
        label="Trials",
        extractor=lambda r: r.trials,
        group="audit",
        align="right",
    )
)

register_column(
    Column(
        key="solved",
        label="Solved",
        extractor=lambda r: r.solved,
        group="audit",
        align="right",
    )
)

register_column(
    Column(
        key="failed",
        label="Failed",
        extractor=lambda r: r.failed,
        group="audit",
        align="right",
    )
)

register_column(
    Column(
        key="slow",
        label="Slow",
        extractor=lambda r: r.slow,
        group="audit",
        align="right",
    )
)

register_column(
    Column(
        key="success_rate",
        label="Success %",
        extractor=lambda r: r.success_rate,
        group="audit",
        align="right",
        fmt="float1",
    )
)


# =========================================================
# VIEWS
# =========================================================

register_view(
    "audit_dashboard",
    [
        "id",
        "case",
        "date",
        "time",
        "runs",
        "trials",
        "solved",
        "failed",
        "slow",
        "success_rate",
    ],
)
