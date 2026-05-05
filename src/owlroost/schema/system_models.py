from pydantic import BaseModel, ConfigDict, Field


class BaseSystemConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")


# =========================================================
# TRIAL
# =========================================================


class TrialConfig(BaseSystemConfig):
    """Configuration for trial execution."""

    id: int = Field(
        default=0,
        description="Trial index within a run.",
    )

    n_jobs: int = Field(
        default=5,
        ge=1,
        description="Parallel jobs for trial execution.",
    )


# =========================================================
# RUNTIME
# =========================================================


class RuntimeConfig(BaseSystemConfig):
    """Runtime parallelization and execution controls."""

    trial_jobs: int = Field(
        default=4,
        ge=1,
        description="Number of parallel trial workers.",
    )

    run_jobs: int = Field(
        default=1,
        ge=1,
        description="Number of parallel runs.",
    )

    worker_timeout: int = Field(
        default=120,
        ge=1,
        description="Timeout in seconds for each trial worker.",
    )

    cpu_reserve: int = Field(
        default=1,
        ge=0,
        description="Number of CPU cores to reserve.",
    )

    oversubscribe_factor: float = Field(
        default=1.0,
        gt=0,
        description="Oversubscription factor for parallelism.",
    )

    enforce_single_axis: bool = Field(
        default=True,
        description="Force single-axis parallelization.",
    )


# =========================================================
# ROOST
# =========================================================


class RoostConfig(BaseSystemConfig):
    """Global Roost configuration."""

    master_seed: int | None = Field(
        default=None,
        description="Master seed for deterministic runs.",
    )

    experiment_id: str | None = Field(
        default=None,
        description="Experiment identifier.",
    )

    description: str | None = Field(
        default=None,
        description="Optional description of experiment.",
    )

    trials_per_run: int = Field(
        default=1,
        ge=1,
        description="Number of trials per run.",
    )


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
    """Hydra-level case selection configuration."""

    file: str | None = Field(
        default=None,
        description="Path to case TOML file.",
    )

    name: str | None = Field(
        default=None,
        description="Case name override.",
    )
