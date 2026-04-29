from pydantic import BaseModel

# =========================================================
# CORE SMALL STRUCTURES
# =========================================================


class ValueFutureToday(BaseModel):
    future: float
    today: float


class TotalFutureToday(BaseModel):
    future: float
    today: float


# =========================================================
# FINANCIAL
# =========================================================


class Spending(BaseModel):
    year0: ValueFutureToday
    total: TotalFutureToday


class SpendingProfile(BaseModel):
    year0: float
    early_avg: float
    late_avg: float
    yearN: float
    survivor_ratio: float | None


class Taxes(BaseModel):
    total: TotalFutureToday


class Roth(BaseModel):
    total: TotalFutureToday


class Bequest(BaseModel):
    total: TotalFutureToday


class SpendingSummary(BaseModel):
    min_ratio: float | None
    mean_ratio: float | None
    median_ratio: float | None
    p10_ratio: float | None = None
    std_ratio: float | None = None

    years_under_target: int | None

    min_ratio_to_essential: float | None
    mean_ratio_to_essential: float | None
    median_ratio_to_essential: float | None

    min_ratio_to_lifestyle: float | None
    mean_ratio_to_lifestyle: float | None
    median_ratio_to_lifestyle: float | None

    years_below_essential: int | None
    years_below_lifestyle: int | None

    consecutive_years_below_lifestyle: int | None
    consecutive_years_below_essential: int | None

    lifestyle_stress_flag: int | None
    essential_spending_breach: int | None


class Inflation(BaseModel):
    final_factor: float


class InflationTS(BaseModel):
    factor_by_year: list[float]


class AssetsTS(BaseModel):
    future_by_year: list[float]
    today_by_year: list[float]


class SpendingTS(BaseModel):
    future_by_year: list[float]
    today_by_year: list[float]


class TimeSeries(BaseModel):
    inflation: InflationTS | None = None
    assets: AssetsTS | None = None
    spending: SpendingTS | None = None


class Financial(BaseModel):
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


class RiskSummary(BaseModel):
    overall_risk: str | None
    scenario_severity: float | None
    depleted: bool | None
    worst_drawdown: float | None
    terminal_ratio: float | None
    flag_count: int | None
    flags: list[str]


class RiskScenario(BaseModel):
    valid: bool
    horizon: int | None = None

    returns: dict[str, float] | None = None
    drawdown: dict[str, float] | None = None
    inflation: dict[str, float] | None = None
    real: dict[str, float] | None = None

    classification: dict[str, str] | None = None
    severity_score: float | None = None
    flags: list[str] | None = None


class RiskOutcome(BaseModel):
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
    flags: list[str] | None = None


class Risk(BaseModel):
    scenario: RiskScenario | None = None
    outcome: RiskOutcome | None = None
    summary: RiskSummary | None = None


# =========================================================
# COMPLEXITY
# =========================================================


class Complexity(BaseModel):
    num_decision_variables: int | None
    num_constraints: int | None
    num_nonzeros: int | None
    matrix_density: float | None
    num_integer_variables: int | None
    integer_variable_ratio: float | None
    horizon: int | None
    nnz_per_variable: float | None
    nnz_per_constraint: float | None


# =========================================================
# SOCIAL SECURITY
# =========================================================


class SocialSecurity(BaseModel):
    optimized: bool | None
    ages: list[float] | None


# =========================================================
# RATES
# =========================================================


class Rates(BaseModel):
    valid: bool | None

    returns: dict[str, float] | None = None
    bonds: dict[str, float] | None = None
    inflation: dict[str, float] | None = None
    real: dict[str, float] | None = None

    early: dict[str, float] | None = None


# =========================================================
# SCORE
# =========================================================


class Score(BaseModel):
    score: float


# =========================================================
# RUN STATUS
# =========================================================


class RunStatus(BaseModel):
    status: str
    failure_category: str | None
    failure_subtype: str | None
    failure_detail: str | None


# =========================================================
# IDENTITY
# =========================================================


class Identity(BaseModel):
    plan_name: str


# =========================================================
# METRICS MODEL (TOP LEVEL)
# =========================================================


class MetricsModel(BaseModel):
    schema_version: str

    identity: Identity
    run_status: RunStatus
    timing: dict[str, float]

    solver: str | None

    financial: Financial
    risk: Risk
    complexity: Complexity
    social_security: SocialSecurity
    rates: Rates
    score: Score
