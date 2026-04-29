from pathlib import Path

from ..registry import Column, register_column, register_view

# =========================================================
# CORE IDENTIFIERS
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

# =========================================================
# EXPERIMENT STATS
# =========================================================

register_column(
    Column(
        key="runs",
        label="Runs",
        extractor=lambda r: r.runs,
        group="stats",
        align="right",
    )
)

register_column(
    Column(
        key="trials",
        label="Trials",
        extractor=lambda r: r.trials,
        group="stats",
        align="right",
    )
)

register_column(
    Column(
        key="solved",
        label="Solved",
        extractor=lambda r: r.solved,
        group="stats",
        align="right",
    )
)

register_column(
    Column(
        key="failed",
        label="Failed",
        extractor=lambda r: r.failed,
        group="stats",
        align="right",
    )
)

register_column(
    Column(
        key="slow",
        label="Slow",
        extractor=lambda r: r.slow,
        group="stats",
        align="right",
    )
)

register_column(
    Column(
        key="success_rate",
        label="Success %",
        extractor=lambda r: r.success_rate,
        group="stats",
        align="right",
        fmt="float1",
    )
)

# =========================================================
# RUNTIME
# =========================================================

register_column(
    Column(
        key="runtime",
        label="Time (s)",
        extractor=lambda r: r.runtime,
        group="runtime",
        align="right",
        fmt="float2",
    )
)

# =========================================================
# FINANCIAL METRICS
# =========================================================

register_column(
    Column(
        key="spend_basis",
        label="Spend",
        extractor=lambda r: r.spend_basis,
        group="financial",
        align="right",
        fmt="float1_k",
    )
)

register_column(
    Column(
        key="total_spend_real",
        label="Tot Spend",
        extractor=lambda r: r.total_spend_real,
        group="financial",
        align="right",
        fmt="float1_k",
    )
)

register_column(
    Column(
        key="bequest_real",
        label="Bequest",
        extractor=lambda r: r.bequest_real,
        group="financial",
        align="right",
        fmt="float1_k",
    )
)

# =========================================================
# COMPLEXITY METRICS
# =========================================================

register_column(
    Column(
        key="nvars",
        label="Vars",
        extractor=lambda r: r.nvars,
        group="complexity",
        align="right",
        fmt="int",
    )
)

register_column(
    Column(
        key="ncons",
        label="Cons",
        extractor=lambda r: r.ncons,
        group="complexity",
        align="right",
        fmt="int",
    )
)

register_column(
    Column(
        key="nnz",
        label="NNZ",
        extractor=lambda r: r.nnz,
        group="complexity",
        align="right",
        fmt="int",
    )
)

register_column(
    Column(
        key="int_ratio",
        label="Int %",
        extractor=lambda r: r.int_ratio,
        group="complexity",
        align="right",
        fmt="percent1",
    )
)


# =========================================================
# TRIAL-LEVEL
# =========================================================

register_column(
    Column(
        key="trial_id",
        label="ID",
        extractor=lambda r: Path(r.path).name if r.path else None,
        group="failure",
        align="right",
    )
)

register_column(
    Column(
        key="failure_category",
        label="Category",
        extractor=lambda r: r.failure_category,
        group="failure",
        align="left",
    )
)

register_column(
    Column(
        key="failure_detail",
        label="Detail",
        extractor=lambda r: r.failure_detail,
        group="failure",
        align="left",
    )
)

register_column(
    Column(
        key="status",
        label="Status",
        extractor=lambda r: r.status,
        group="failure",
        align="left",
    )
)

register_column(
    Column(
        key="path",
        label="Path",
        extractor=lambda r: str(r.path),
        group="failure",
        align="left",
    )
)

register_column(
    Column(
        key="trial_id",
        label="ID",
        extractor=lambda r: r.trial_id,
        group="failure",
        align="right",
    )
)

register_column(
    Column(
        key="failure_year",
        label="Year",
        extractor=lambda r: r.cumulative_real_failure_year,
        group="failure",
        align="right",
    )
)

register_column(
    Column(
        key="withdrawal_pressure",
        label="W/S",
        extractor=lambda r: r.withdrawal_to_spending_ratio,
        fmt=".2f",
        group="failure",
        align="right",
    )
)


# =========================================================
# VIEWS
# =========================================================

# --- Core dashboard (unchanged behavior) ---

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

# --- Runtime + financial diagnostics ---

register_view(
    "audit_runtime",
    [
        "id",
        "case",
        "trials",
        "runtime",
        "spend_basis",
        "total_spend_real",
        "bequest_real",
        "success_rate",
    ],
)

# --- Complexity diagnostics ---

register_view(
    "audit_complexity",
    [
        "id",
        "case",
        "nvars",
        "ncons",
        "nnz",
        "int_ratio",
        "success_rate",
    ],
)

# --- Full diagnostic view (recommended default for power users) ---

register_view(
    "audit_full",
    [
        "id",
        "case",
        "runtime",
        "runs",
        "trials",
        "solved",
        "failed",
        "success_rate",
        "spend_basis",
        "total_spend_real",
        "bequest_real",
        "nvars",
        "ncons",
        "nnz",
        "int_ratio",
    ],
)

# --- Failure examples (trial-level) ---

register_view(
    "audit_failure_examples",
    [
        "failure_category",
        "failure_year",  # 🔥 new
        "withdrawal_pressure",  # 🔥 new
        "status",
        "runtime",
    ],
)
