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

    count: int = Field(
        default=1,
        ge=1,
        description="Number of trials per run.",
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
