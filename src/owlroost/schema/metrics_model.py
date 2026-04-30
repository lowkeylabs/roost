from pydantic import BaseModel, ConfigDict, Field

# =========================================================
# BASE
# =========================================================


class BaseMetricsModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


# =========================================================
# CORE SMALL STRUCTURES
# =========================================================


class ValueFutureToday(BaseMetricsModel):
    future: float
    today: float


# =========================================================
# FINANCIAL
# =========================================================


class Spending(BaseMetricsModel):
    year0: ValueFutureToday | None = None
    total: ValueFutureToday | None = None


class SpendingProfile(BaseMetricsModel):
    year0: float
    early_avg: float
    late_avg: float
    yearN: float
    survivor_ratio: float | None = None


class Taxes(BaseMetricsModel):
    total: ValueFutureToday | None = None


class Roth(BaseMetricsModel):
    total: ValueFutureToday | None = None


class Bequest(BaseMetricsModel):
    total: ValueFutureToday | None = None


class SpendingSummary(BaseMetricsModel):
    min_ratio: float | None = None
    mean_ratio: float | None = None
    median_ratio: float | None = None
    p10_ratio: float | None = None
    std_ratio: float | None = None

    years_under_target: int | None = None

    min_ratio_to_essential: float | None = None
    mean_ratio_to_essential: float | None = None
    median_ratio_to_essential: float | None = None

    min_ratio_to_lifestyle: float | None = None
    mean_ratio_to_lifestyle: float | None = None
    median_ratio_to_lifestyle: float | None = None

    years_below_essential: int | None = None
    years_below_lifestyle: int | None = None

    consecutive_years_below_lifestyle: int | None = None
    consecutive_years_below_essential: int | None = None

    lifestyle_stress_flag: int | None = None
    essential_spending_breach: int | None = None


class Inflation(BaseMetricsModel):
    final_factor: float


class InflationTS(BaseMetricsModel):
    factor_by_year: list[float] = Field(default_factory=list)


class AssetsTS(BaseMetricsModel):
    future_by_year: list[float] = Field(default_factory=list)
    today_by_year: list[float] = Field(default_factory=list)


class SpendingTS(BaseMetricsModel):
    future_by_year: list[float] = Field(default_factory=list)
    today_by_year: list[float] = Field(default_factory=list)


class TimeSeries(BaseMetricsModel):
    inflation: InflationTS | None = None
    assets: AssetsTS | None = None
    spending: SpendingTS | None = None


class Financial(BaseMetricsModel):
    valid: bool

    spending: Spending | None = None
    spending_profile: SpendingProfile | None = None
    taxes: Taxes | None = None
    roth: Roth | None = None
    bequest: Bequest | None = None

    spending_summary: SpendingSummary | None = None

    inflation: Inflation | None = None
    timeseries: TimeSeries | None = None


# =========================================================
# RISK
# =========================================================


class RiskSummary(BaseMetricsModel):
    overall_risk: str | None = None
    scenario_severity: float | None = None
    depleted: bool | None = None
    worst_drawdown: float | None = None
    terminal_ratio: float | None = None
    flag_count: int | None = None
    flags: list[str] = Field(default_factory=list)


class RiskScenario(BaseMetricsModel):
    valid: bool
    horizon: int | None = None

    returns: dict[str, float] | None = None
    drawdown: dict[str, float] | None = None
    inflation: dict[str, float] | None = None
    real: dict[str, float] | None = None

    classification: dict[str, str] | None = None
    severity_score: float | None = None
    flags: list[str] = Field(default_factory=list)


class RiskOutcome(BaseMetricsModel):
    valid: bool
    horizon: int | None = None

    assets: dict[str, float] | None = None
    depletion: dict | None = None
    sustainability: dict | None = None
    fragility: dict | None = None
    drawdown: dict | None = None
    terminal: dict | None = None
    cushion: dict | None = None
    consumption: dict | None = None

    classification: dict[str, str] | None = None
    flags: list[str] = Field(default_factory=list)


class Risk(BaseMetricsModel):
    scenario: RiskScenario | None = None
    outcome: RiskOutcome | None = None
    summary: RiskSummary | None = None


# =========================================================
# COMPLEXITY
# =========================================================


class Complexity(BaseMetricsModel):
    num_decision_variables: int | None = None
    num_constraints: int | None = None
    num_nonzeros: int | None = None
    matrix_density: float | None = None
    num_integer_variables: int | None = None
    integer_variable_ratio: float | None = None
    horizon: int | None = None
    nnz_per_variable: float | None = None
    nnz_per_constraint: float | None = None


# =========================================================
# SOCIAL SECURITY
# =========================================================


class SocialSecurity(BaseMetricsModel):
    optimized: bool | None = None
    ages: list[float] = Field(default_factory=list)


# =========================================================
# RATES
# =========================================================


class Rates(BaseMetricsModel):
    valid: bool | None = None

    returns: dict[str, float] | None = None
    bonds: dict[str, float] | None = None
    inflation: dict[str, float] | None = None
    real: dict[str, float] | None = None

    early: dict[str, float] | None = None


# =========================================================
# SCORE
# =========================================================


class Score(BaseMetricsModel):
    score: float


# =========================================================
# RUN STATUS
# =========================================================


class RunStatus(BaseMetricsModel):
    status: str
    failure_category: str | None = None
    failure_subtype: str | None = None
    failure_detail: str | None = None


# =========================================================
# IDENTITY
# =========================================================


class Identity(BaseMetricsModel):
    plan_name: str


# =========================================================
# TIMING (NEW — replaces dict)
# =========================================================


class Timing(BaseMetricsModel):
    solve_start: float | None = None
    solve_end: float | None = None
    elapsed_seconds: float | None = None


# =========================================================
# METRICS MODEL (TOP LEVEL)
# =========================================================


class MetricsModel(BaseMetricsModel):
    schema_version: str

    identity: Identity
    run_status: RunStatus
    timing: Timing

    solver: str | None = None

    financial: Financial
    risk: Risk
    complexity: Complexity
    social_security: SocialSecurity
    rates: Rates
    score: Score
