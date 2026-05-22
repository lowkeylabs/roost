from pydantic import BaseModel, ConfigDict, Field

# =========================================================
# Base
# =========================================================


class BaseSystemConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")


# =========================================================
# ROOST RUNTIME
# =========================================================


class RoostRuntimeConfig(BaseSystemConfig):
    """
    ROOST execution/orchestration configuration.

    These settings define HOW ROOST executes
    sessions and trials, separate from the
    retirement scenario itself.
    """

    # -----------------------------------------------------
    # Session provenance
    # -----------------------------------------------------

    session_id: str | None = Field(
        default=None,
        description="Session identifier.",
    )

    session_description: str | None = Field(
        default=None,
        description="Optional session description.",
    )

    run_id: int | None = Field(
        default=None,
        ge=0,
        description="Run index within session.",
    )

    run_description: str | None = Field(
        default=None,
        description="Optional run description.",
    )

    trial_id: int | None = Field(
        default=None,
        ge=0,
        description="Trial index within run.",
    )

    # -----------------------------------------------------
    # Deterministic execution
    # -----------------------------------------------------

    master_seed: int | None = Field(
        default=987_654_321,
        description="Master seed for deterministic execution.",
    )

    rate_seed: int | None = Field(
        default=None,
        description="Seed used for stochastic rates generation.",
    )

    longevity_seed: int | None = Field(
        default=None,
        description="Seed used for stochastic longevity generation.",
    )

    # -----------------------------------------------------
    # Trial generation
    # -----------------------------------------------------

    trials_per_run: int = Field(
        default=1,
        ge=1,
        description="Number of trials generated for each run.",
    )

    # -----------------------------------------------------
    # Parallel execution
    # -----------------------------------------------------

    workers_per_run: int | None = Field(
        default=None,
        ge=1,
        description=("Number of parallel workers used " "to execute trials within a run."),
    )

    worker_timeout: int = Field(
        default=120,
        ge=1,
        description="Timeout in seconds for each trial.",
    )

    run_owl_as_subprocess: bool = Field(
        default=False,
        description="Execute OWL in a subprocess.",
    )

    workers_per_run_mode: str = Field(
        default="auto",
        description=("Worker allocation strategy: " "'fixed' or 'auto'."),
    )

    # -----------------------------------------------------
    # Solver-aware execution topology policies
    # -----------------------------------------------------

    auto_workers_by_solver: dict[str, int] = Field(
        default_factory=lambda: {
            # -----------------------------------------
            # MOSEK:
            #
            # Fewer heavier workers.
            # Strong evidence that many
            # single-threaded workers perform best.
            # -----------------------------------------
            "MOSEK": 8,
            # -----------------------------------------
            # HiGHS:
            #
            # More lighter-weight workers.
            # -----------------------------------------
            "HiGHS": 12,
        },
        description=(
            "Recommended workers_per_run " "by solver when " "workers_per_run_mode='auto'."
        ),
    )

    auto_runtime_environment_by_solver: dict[str, dict[str, int]] = Field(
        default_factory=lambda: {
            # -----------------------------------------
            # MOSEK:
            #
            # Strong evidence that nested threading
            # hurts throughput.
            #
            # Prefer many independent
            # single-threaded solves.
            # -----------------------------------------
            "MOSEK": {
                "OMP_NUM_THREADS": 1,
                "OPENBLAS_NUM_THREADS": 1,
                "MKL_NUM_THREADS": 1,
                "MSK_IPAR_NUM_THREADS": 1,
            },
            # -----------------------------------------
            # HiGHS:
            #
            # Current evidence suggests explicit
            # thread forcing is unnecessary and
            # sometimes harmful.
            #
            # Leave runtime environment unset.
            # -----------------------------------------
            "HiGHS": {},
        },
        description=(
            "Recommended runtime environment "
            "variables by solver when "
            "workers_per_run_mode='auto'."
        ),
    )


# =========================================================
# RUNTIME ENVIRONMENT
# =========================================================


class RuntimeEnvironmentConfig(BaseSystemConfig):
    """
    Process-level runtime environment variables.

    These settings control BLAS/OpenMP/MOSEK/etc.
    threading and low-level runtime behavior.
    """

    OMP_NUM_THREADS: int | None = Field(
        default=None,
        ge=1,
        description="OpenMP thread count.",
    )

    OPENBLAS_NUM_THREADS: int | None = Field(
        default=None,
        ge=1,
        description="OpenBLAS thread count.",
    )

    MKL_NUM_THREADS: int | None = Field(
        default=None,
        ge=1,
        description="Intel MKL thread count.",
    )

    MSK_IPAR_NUM_THREADS: int | None = Field(
        default=None,
        ge=1,
        description="MOSEK thread count.",
    )


# =========================================================
# ROOST LONGEVITY MODEL
# Separate from OWL longevity settings
# =========================================================


class LongevityConfig(BaseSystemConfig):
    apply_to_plan: bool = Field(
        default=False,
        description="Whether longevity modeling is applied to the plan.",
    )

    use_stochastic_model: bool = Field(
        default=False,
        description="Enable stochastic longevity modeling.",
    )

    life_expectancy_seed: int | None = Field(
        default=None,
        description="Seed used for stochastic life expectancy modeling.",
    )

    model_name: str | None = Field(
        default=None,
        description="Name of the longevity model to use.",
    )

    partnered: bool = Field(
        default=False,
        description="Indicates whether the household is partnered.",
    )

    lifetime_percentile: list[float] | None = Field(
        default=None,
        description="Target lifetime percentile(s) for longevity modeling.",
    )

    sex: list[str] | None = Field(
        default=None,
        description="Sex for each individual in longevity modeling.",
    )

    health: list[str] | None = Field(
        default=None,
        description="Health status for each individual.",
    )

    smoker: list[bool] | None = Field(
        default=None,
        description="Smoking status for each individual.",
    )


# =========================================================
# SPENDING POLICY
# =========================================================


class SpendingPolicyConfig(BaseSystemConfig):
    essential_spending: float = Field(
        default=0.0,
        description="Minimum essential spending level.",
    )

    lifestyle_spending: float = Field(
        default=0.0,
        description="Desired lifestyle spending level above essentials.",
    )

    baseline_years: int = Field(
        default=3,
        ge=0,
        description="Number of baseline years used for spending evaluation.",
    )

    max_years_below_threshhold: int = Field(
        default=5,
        ge=0,
        description="Maximum allowed years below spending threshold.",
    )

    max_consecutive_years_below_threshhold: int = Field(
        default=5,
        ge=0,
        description="Maximum consecutive years allowed below threshold.",
    )


# =========================================================
# CASE
# =========================================================


class CaseConfig(BaseSystemConfig):
    """
    Hydra-level case selection configuration.
    """

    file: str | None = Field(
        default=None,
        description="Path to case TOML file.",
    )

    name: str | None = Field(
        default=None,
        description="Case name override.",
    )
