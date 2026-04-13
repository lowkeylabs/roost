import ast
import os
import re
import secrets
from datetime import date, datetime
from io import StringIO
from pathlib import Path
from typing import Any, ClassVar

from owlplanner.config.plan_bridge import config_to_plan
from owlplanner.config.schema import config_dict_to_model
from owlplanner.config.toml_io import load_toml, save_toml
from pydantic import BaseModel, Field, field_validator

from owlroost.core.longevity import deterministic_individual_lifetime

# helpers


def _resolve_spending_value(value, baseline):
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()

        if value.endswith("%"):
            try:
                pct = float(value[:-1]) / 100.0
                return pct * baseline  # already dollars
            except Exception:
                return None

    try:
        return float(value)  # still in user units
    except Exception:
        return None


def _apply_units(value, case):
    if value is None:
        return None

    solver = getattr(case.config, "solver_options", None)

    if isinstance(solver, dict):
        units = solver.get("units", "k")
    else:
        units = getattr(solver, "units", "k")

    if units == "k":
        return value * 1_000
    if units == "M":
        return value * 1_000_000

    return value  # assume already dollars


def _get_input_baseline(case):
    """
    Resolve baseline spending from inputs ONLY.
    Works without running the solver.
    """

    obj = case.objective
    solver = getattr(case.config, "solver_options", None)

    if solver is None:
        return 0.0

    # Handle both object and dict
    if isinstance(solver, dict):
        get = solver.get
    else:

        def get(k, default=None):
            return getattr(solver, k, default)

    if obj == "maxBequest":
        val = get("netSpending")
    elif obj == "maxSpending":
        return None
    else:
        val = None

    if val is None:
        return 0.0

    # Handle units
    units = get("units", "k")

    v = float(val)

    if units == "k":
        return v * 1_000
    if units == "M":
        return v * 1_000_000

    return v


def get_effective_spending_policy(case, baseline=None):
    # ----------------------------------------
    # Safety: no case
    # ----------------------------------------
    if case is None:
        return {
            "minimum_spending": 0,
            "acceptable_spending": 0,
            "baseline_years": 3,
            "max_years_below_acceptable": 5,
            "max_consecutive_years_below_acceptable": 5,
        }

    policy = case.spending_policy

    # ----------------------------------------
    # Baseline resolution (CRITICAL FIX)
    # ----------------------------------------
    # Use provided baseline FIRST (solution-derived)
    if not isinstance(baseline, (int, float)) or not (baseline and baseline > 0):
        try:
            baseline = _get_input_baseline(case)
        except Exception:
            baseline = None

    # Normalize invalid baseline → None
    if not isinstance(baseline, (int, float)) or not (baseline and baseline > 0):
        baseline = None

    # ----------------------------------------
    # No policy → defaults
    # ----------------------------------------
    if not policy:
        if baseline is None:
            return {
                "minimum_spending": None,
                "acceptable_spending": None,
                "baseline_years": 3,
                "max_years_below_acceptable": 5,
                "max_consecutive_years_below_acceptable": 5,
            }

        return {
            "minimum_spending": 0.7 * baseline,
            "acceptable_spending": 1.0 * baseline,
            "baseline_years": 3,
            "max_years_below_acceptable": 5,
            "max_consecutive_years_below_acceptable": 5,
        }

    # ----------------------------------------
    # Resolve values (SAFE)
    # ----------------------------------------
    def safe_resolve(value):
        if isinstance(value, str) and value.strip().endswith("%"):
            if baseline is None:
                return None
            try:
                pct = float(value.strip()[:-1]) / 100.0
                return pct * baseline
            except Exception:
                return None

        try:
            return float(value)
        except Exception:
            return None

    minimum = safe_resolve(policy.minimum_spending)
    acceptable = safe_resolve(policy.acceptable_spending)

    # ----------------------------------------
    # Apply units normalization
    # ----------------------------------------

    # Only apply units if value came from numeric input (not %)
    def maybe_apply_units(raw_value, resolved_value):
        if isinstance(raw_value, str) and raw_value.strip().endswith("%"):
            return resolved_value  # already dollars
        return _apply_units(resolved_value, case)

    minimum = maybe_apply_units(policy.minimum_spending, minimum)
    acceptable = maybe_apply_units(policy.acceptable_spending, acceptable)

    # ----------------------------------------
    # Fallback if parsing failed
    # ----------------------------------------
    if baseline is not None:
        if minimum is None:
            minimum = 0.7 * baseline
        if acceptable is None:
            acceptable = 1.0 * baseline

    # ----------------------------------------
    # Final safety (prevent None propagation)
    # ----------------------------------------
    if minimum is None or acceptable is None:
        return {
            "minimum_spending": None,
            "acceptable_spending": None,
            "baseline_years": policy.baseline_years,
            "max_years_below_acceptable": policy.max_years_below_acceptable,
            "max_consecutive_years_below_acceptable": policy.max_consecutive_years_below_acceptable,
        }

    # ----------------------------------------
    # Validation
    # ----------------------------------------
    if acceptable < minimum:
        acceptable = minimum  # soften instead of raising

    return {
        "minimum_spending": float(minimum),
        "acceptable_spending": float(acceptable),
        "baseline_years": policy.baseline_years,
        "max_years_below_acceptable": policy.max_years_below_acceptable,
        "max_consecutive_years_below_acceptable": policy.max_consecutive_years_below_acceptable,
    }


# =========================================================
# ROOST Extension Schemas
# =========================================================


class LongevityConfig(BaseModel):
    DEFAULT_PERCENTILE: ClassVar[float] = 0.80
    DEFAULT_SEX: ClassVar[str] = "female"
    DEFAULT_HEALTH: ClassVar[str] = "average"
    DEFAULT_SMOKER: ClassVar[bool] = False
    DEFAULT_APPLY_TO_PLAN: ClassVar[bool] = False
    DEFAULT_USE_STOCHASTIC_MODEL: ClassVar[bool] = False
    DEFAULT_LIFE_EXPECTANCY_SEED: ClassVar[int] = 1_234_567_890
    DEFAULT_MODEL_NAME: ClassVar[str] = "default"

    apply_to_plan: bool = DEFAULT_APPLY_TO_PLAN
    use_stochastic_model: bool = DEFAULT_USE_STOCHASTIC_MODEL
    life_expectancy_seed: int | None = DEFAULT_LIFE_EXPECTANCY_SEED
    model_name: str = DEFAULT_MODEL_NAME
    partnered: bool = True

    lifetime_percentile: list[float] = Field(
        default_factory=lambda: [LongevityConfig.DEFAULT_PERCENTILE]
    )
    sex: list[str] = Field(default_factory=lambda: [LongevityConfig.DEFAULT_SEX])
    health: list[str] = Field(default_factory=lambda: [LongevityConfig.DEFAULT_HEALTH])
    smoker: list[bool] = Field(default_factory=lambda: [LongevityConfig.DEFAULT_SMOKER])

    @field_validator("lifetime_percentile")
    @classmethod
    def _validate_percentile_range(cls, v):
        if not v:
            raise ValueError("lifetime_percentile cannot be empty.")
        for p in v:
            if not (0.0 < p <= 1.0):
                raise ValueError("lifetime_percentile must be in (0,1].")
        return v

    @field_validator("health", mode="before")
    @classmethod
    def _coerce_health(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return list(v)

    @field_validator("smoker", mode="before")
    @classmethod
    def _coerce_smoker(cls, v):
        if v is None:
            return []
        if isinstance(v, bool):
            return [v]
        return list(v)

    def resized(self, n: int) -> "LongevityConfig":
        """
        Return a new LongevityConfig resized to household size n,
        using schema defaults for any newly created entries.
        """

        def resize(values, default):
            if len(values) < n:
                return values + [default] * (n - len(values))
            return values[:n]

        return LongevityConfig(
            apply_to_plan=self.apply_to_plan,
            use_stochastic_model=self.use_stochastic_model,
            life_expectancy_seed=self.life_expectancy_seed,
            partnered=(n == 2),
            lifetime_percentile=resize(
                self.lifetime_percentile,
                self.DEFAULT_PERCENTILE,
            ),
            sex=resize(self.sex, self.DEFAULT_SEX),
            health=resize(self.health, self.DEFAULT_HEALTH),
            smoker=resize(self.smoker, self.DEFAULT_SMOKER),
        )


class RoostConfig(BaseModel):
    master_seed: int = Field(default_factory=lambda: secrets.randbits(32))
    trials: int = 1
    experiment: str | None = None


class SpendingPolicyConfig(BaseModel):
    minimum_spending: float | int | None = 80.0
    acceptable_spending: float | int | str = "100%"
    baseline_years: int = 3
    max_years_below_acceptable: int = 5
    max_consecutive_years_below_acceptable: int = 5


class CacheConfig(BaseModel):
    generated_at: str  # ISO timestamp

    retirement_horizon: int | None = None
    max_spending: float | None = None
    first_year_total_withdrawals: float | None = None


EXTRA_SECTION_REGISTRY: dict[str, type[BaseModel]] = {
    "spending_policy": SpendingPolicyConfig,
    "longevity": LongevityConfig,
    "roost": RoostConfig,
    "cache": CacheConfig,
}

# =========================================================
# Case
# =========================================================


class Case:
    def __init__(self, path: Path):
        self.path = path
        self._raw_dict, _, _ = load_toml(str(path))
        self.config, self.extra = config_dict_to_model(self._raw_dict)

        self.extensions: dict[str, BaseModel] = {}

        for section_name, schema in EXTRA_SECTION_REGISTRY.items():
            section_data = self.extra.get(section_name)
            if section_data is not None:
                model = schema(**section_data)
                if section_name == "longevity":
                    model = self._align_longevity(model)
                self.extensions[section_name] = model

    # =========================================================
    # Mutation Engine
    # =========================================================

    @staticmethod
    def _parse_literal(value: str) -> Any:
        value = value.strip()

        # ----------------------------------------
        # Try Python literal first
        # ----------------------------------------
        try:
            return ast.literal_eval(value)
        except Exception:
            pass

        # ----------------------------------------
        # Normalize booleans
        # ----------------------------------------
        lowered = value.lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        if lowered == "none":
            return None

        # ----------------------------------------
        # Handle bracket lists without quotes
        # Example: [excellent,excellent]
        # ----------------------------------------
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            if not inner:
                return []

            parts = [x.strip() for x in inner.split(",")]
            return [Case._parse_literal(x) for x in parts]

        # ----------------------------------------
        # Handle comma-separated lists
        # Example: excellent,excellent
        # ----------------------------------------
        if "," in value:
            parts = [x.strip() for x in value.split(",")]
            return [Case._parse_literal(x) for x in parts]

        # ----------------------------------------
        # Try numeric conversion
        # ----------------------------------------
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        # ----------------------------------------
        # Fallback: raw string
        # ----------------------------------------
        return value

    @staticmethod
    def _parse_lhs(lhs: str):
        match = re.match(r"(\w+)\.(\w+)(?:\[(\d+)\])?$", lhs)
        if not match:
            raise ValueError(f"Invalid mutation path: {lhs}")
        section, field, index = match.groups()
        return section, field, int(index) if index else None

    def apply_mutation(self, assignment: str) -> None:
        if "=" not in assignment:
            raise ValueError("Mutation must be of form section.field=value")

        lhs, rhs = assignment.split("=", 1)
        lhs = lhs.strip()
        value = self._parse_literal(rhs.strip())

        section, field, index = self._parse_lhs(lhs)

        if section in self.extensions:
            container = self.extensions[section]
        elif hasattr(self.config, section):
            container = getattr(self.config, section)
        else:
            raise ValueError(f"Unknown section '{section}'")

        if not hasattr(container, field):
            raise ValueError(f"Section [{section}] has no field '{field}'")

        current = getattr(container, field)

        if index is not None:
            if not isinstance(current, list):
                raise ValueError(f"{field} is not a list")
            if index >= len(current):
                raise IndexError(f"Index {index} out of range")
            current[index] = value
            setattr(container, field, current)
        else:
            setattr(container, field, value)

        self._rebuild_case()

    def _rebuild_case(self):
        if hasattr(self.config, "model_dump"):
            core_dict = self.config.model_dump(by_alias=True)
        else:
            core_dict = self.config.dict()

        updated = dict(self._raw_dict)

        for k, v in core_dict.items():
            updated[k] = v

        for name, model in self.extensions.items():
            updated[name] = model.model_dump(exclude_none=True, by_alias=True)

        self._raw_dict = updated
        self.config, self.extra = config_dict_to_model(updated)

        self.extensions = {}
        for section_name, schema in EXTRA_SECTION_REGISTRY.items():
            section_data = self.extra.get(section_name)
            if section_data is not None:
                model = schema(**section_data)
                if section_name == "longevity":
                    model = self._align_longevity(model)
                self.extensions[section_name] = model

    # =========================================================
    # Persistence
    # =========================================================
    def generate_cache(self, write: bool = False) -> None:
        from owlroost.domain.services.levers import compute_levers

        summary = compute_levers(self)

        model = CacheConfig(
            generated_at=datetime.now().isoformat(),
            retirement_horizon=summary.retirement_horizon,
            max_spending=summary.max_spending,
            first_year_total_withdrawals=summary.first_year_total_withdrawals,
        )

        self.extensions["cache"] = model
        self.extra["cache"] = model.model_dump(exclude_none=True, by_alias=True)

        # 🔴 CRITICAL: update raw dict
        self._raw_dict["cache"] = model.model_dump(exclude_none=True, by_alias=True)

        if write:
            self.write()

    def write(self, path: Path | None = None) -> None:
        target_path = Path(path or self.path)
        filename = target_path.name

        if filename.lower().startswith("case_"):
            final_path = str(target_path)
        else:
            final_path = str(target_path.with_name(f"case_{filename}"))

        for name, model in self.extensions.items():
            self.extra[name] = model.model_dump(exclude_none=True, by_alias=True)

        updated_dict = dict(self._raw_dict)
        for name, section in self.extra.items():
            updated_dict[name] = section

        save_toml(updated_dict, final_path)

    # =========================================================
    # Longevity Alignment
    # =========================================================

    def _align_longevity(self, model: LongevityConfig) -> LongevityConfig:
        n = len(self.household_names)

        return LongevityConfig(
            apply_to_plan=model.apply_to_plan,
            use_stochastic_model=model.use_stochastic_model,
            life_expectancy_seed=model.life_expectancy_seed,
            partnered=(n == 2),
            lifetime_percentile=self._resize_list(
                model.lifetime_percentile,
                n,
                LongevityConfig.DEFAULT_PERCENTILE,
            ),
            sex=self._resize_list(
                model.sex,
                n,
                LongevityConfig.DEFAULT_SEX,
            ),
            health=self._resize_list(
                model.health,
                n,
                LongevityConfig.DEFAULT_HEALTH,
            ),
            smoker=self._resize_list(
                model.smoker,
                n,
                LongevityConfig.DEFAULT_SMOKER,
            ),
        )

    @staticmethod
    def _resize_list(values: list, n: int, default):
        if len(values) < n:
            return values + [default] * (n - len(values))
        return values[:n]

    # ---------------------------------------------------------
    # Cache Accessor
    # ---------------------------------------------------------

    @property
    def cache(self) -> CacheConfig | None:
        return self.extensions.get("cache")

    def _cache_is_valid(self) -> bool:
        """
        Cache is valid only if:
        - cache exists
        - cache timestamp >= TOML mtime
        - cache timestamp >= HFP mtime (if exists)
        """

        cache = self.cache
        if cache is None:
            return False

        try:
            cache_time = datetime.fromisoformat(cache.generated_at)
        except Exception:
            return False

        # Compare against TOML file
        toml_mtime = datetime.fromtimestamp(os.path.getmtime(self.path))
        if cache_time < toml_mtime:
            return False

        # Compare against HFP file if present
        hfp_name = self._raw_dict.get("household_financial_profile", {}).get("HFP_file_name")

        if hfp_name and hfp_name != "None":
            hfp_path = self.path.parent / hfp_name
            if hfp_path.exists():
                hfp_mtime = datetime.fromtimestamp(os.path.getmtime(hfp_path))
                if cache_time < hfp_mtime:
                    return False

        return True

    # ---------------------------------------------------------
    # Longevity Accessor Helpers (Required by views)
    # ---------------------------------------------------------

    @property
    def longevity_percentiles(self) -> list[float]:
        if not self.longevity:
            return []
        return self.longevity.lifetime_percentile

    @property
    def longevity_health(self) -> list[str]:
        if not self.longevity:
            return []
        return self.longevity.health

    @property
    def longevity_sex(self) -> list[str]:
        if not self.longevity:
            return []
        return self.longevity.sex

    @property
    def longevity_smoker(self) -> list[bool]:
        if not self.longevity:
            return []
        return self.longevity.smoker

    @property
    def longevity_partnered(self) -> bool | None:
        if not self.longevity:
            return None
        return self.longevity.partnered

    # =========================================================
    # Extension Accessors
    # =========================================================

    @property
    def spending_policy(self) -> SpendingPolicyConfig | None:
        return self.extensions.get("spending_policy")

    @property
    def longevity(self):
        return self.extensions.get("longevity")

    @property
    def roost(self):
        return self.extensions.get("roost")

    @property
    def has_longevity_section(self) -> bool:
        return "longevity" in self.extra

    @property
    def has_roost_section(self) -> bool:
        return "roost" in self.extra

    # =========================================================
    # Original Properties (UNCHANGED)
    # =========================================================

    @property
    def name(self) -> str:
        return self.config.case_name or self.path.name

    @property
    def filename(self) -> str:
        return self.path.name

    @property
    def household_names(self) -> list[str]:
        return self.config.basic_info.names

    @property
    def start_date(self) -> str:
        return self.config.basic_info.start_date

    @property
    def start_year(self) -> int:
        start = self.config.basic_info.start_date
        if hasattr(start, "year"):
            return start.year
        return date.fromisoformat(str(start)).year

    @property
    def plan_years(self) -> int:
        """
        Number of years in the plan.

        Defined as the maximum remaining lifetime among household members:
            max(life_expectancy - current_age)

        Returns 0 if data is unavailable.
        """

        ages = self.ages
        life_exp = self.life_expectancies

        if not ages or not life_exp:
            return 0

        # Ensure aligned lengths
        n = min(len(ages), len(life_exp))

        remaining_years = [life_exp[i] - ages[i] for i in range(n)]

        if not remaining_years:
            return 0

        return max(remaining_years)

    @property
    def taxable_savings(self) -> float:
        return sum(self.config.savings_assets.taxable_savings_balances)

    @property
    def tax_deferred_savings(self) -> float:
        return sum(self.config.savings_assets.tax_deferred_savings_balances)

    @property
    def tax_free_savings(self) -> float:
        return sum(self.config.savings_assets.tax_free_savings_balances)

    @property
    def total_savings(self) -> float:
        return self.taxable_savings + self.tax_deferred_savings + self.tax_free_savings

    @property
    def objective(self) -> str:
        return self.config.optimization_parameters.objective

    @property
    def spending_profile(self) -> str:
        return self.config.optimization_parameters.spending_profile

    @property
    def ages(self) -> list[int]:
        dobs = self.config.basic_info.date_of_birth
        if not dobs:
            return []

        start_year = int(self.start_date.split("-")[0])
        return [start_year - int(dob.split("-")[0]) for dob in dobs]

    @property
    def life_expectancies(self) -> list[int]:
        return self.config.basic_info.life_expectancy

    @property
    def deterministic_life_ages(self) -> list[float]:
        if self.longevity is None:
            return []

        lon = self.longevity
        current_ages = self.ages

        return [
            int(
                round(
                    deterministic_individual_lifetime(
                        current_age=current_ages[i],
                        lifetime_percentile=lon.lifetime_percentile[i],
                        health=lon.health[i],
                        sex=lon.sex[i],
                        smoker=lon.smoker[i],
                        partnered=lon.partnered,
                    )
                )
            )
            for i in range(len(current_ages))
        ]

    @property
    def deterministic_last_survivor_age(self) -> float | None:
        ages = self.deterministic_life_ages
        return max(ages) if ages else None

    @property
    def pension_monthly(self) -> list[float]:
        return self.config.fixed_income.pension_monthly_amounts or []

    @property
    def pension_ages(self) -> list[float]:
        return self.config.fixed_income.pension_ages or []

    @property
    def social_security_pia(self) -> list[int]:
        return self.config.fixed_income.social_security_pia_amounts or []

    @property
    def social_security_ages(self) -> list[float]:
        return self.config.fixed_income.social_security_ages or []

    # ---------------------------------------------------------
    # Asset Allocation
    # ---------------------------------------------------------

    @property
    def initial_asset_allocation(self) -> list[list[int]]:
        alloc = self.config.asset_allocation

        if not alloc or not getattr(alloc, "generic", None):
            return []

        generic = alloc.generic
        result = []

        for person in generic:
            if not person:
                continue
            result.append(person[0])

        return result

    @property
    def allocation_sentence(self) -> str:
        allocs = self.initial_asset_allocation

        if not allocs:
            return ""

        if all(a == allocs[0] for a in allocs):
            alloc = allocs[0]
            return self._allocation_vector_to_sentence(alloc)

        parts = []
        for name, alloc in zip(self.household_names, allocs, strict=False):
            parts.append(f"{name}: {self._allocation_vector_to_sentence(alloc)}")

        return " Initial allocations are " + "; ".join(parts) + "."

    def _allocation_vector_to_sentence(self, alloc: list[int]) -> str:
        labels = ["equities", "bonds", "Treasury notes", "cash"]

        components = [(pct, label) for pct, label in zip(alloc, labels, strict=False) if pct > 0]

        if not components:
            return "no invested assets"

        if len(components) == 1:
            pct, label = components[0]
            return f"{pct}% {label}"

        if len(components) == 2:
            (p1, l1), (p2, l2) = components
            return f"{p1}% {l1} and {p2}% {l2}"

        parts = [f"{pct}% {label}" for pct, label in components]
        return ", ".join(parts[:-1]) + f", and {parts[-1]}"

    # ---------------------------------------------------------
    # Professional Summary
    # ---------------------------------------------------------

    @property
    def professional_summary(self) -> str:
        names = self.household_names
        ages = self.ages
        life_exp = self.life_expectancies
        start_year = self.start_year

        people = []
        for name, age in zip(names, ages, strict=False):
            people.append(f"{name} ({age})")

        people_str = " and ".join(people)

        total = self.total_savings
        if total >= 1000:
            total_str = f"${total/1000:.1f}M"
        else:
            total_str = f"${total:,.0f}k"

        ss = self.social_security_pia
        pensions = self.pension_monthly

        income_parts = []

        if any(s > 0 for s in ss):
            income_parts.append("Social Security")
        if any(p > 0 for p in pensions):
            income_parts.append("pension income")

        income_sentence = ""
        if income_parts:
            income_sentence = " They expect " + " and ".join(income_parts) + "."

        longevity_sentence = ""
        if life_exp:
            longevity_sentence = (
                " Longevity assumptions extend to ages "
                + " and ".join(str(x) for x in life_exp)
                + "."
            )

        allocation_sentence = ""
        alloc_text = self.allocation_sentence
        if alloc_text:
            allocation_sentence = f" Their initial portfolio allocation is {alloc_text}."

        return (
            f"{people_str} begin planning in {start_year}. "
            f"They hold approximately {total_str} in investable assets."
            f"{income_sentence}"
            f"{allocation_sentence}"
            f"{longevity_sentence}"
        )

    # =========================================================
    # Solver-Based Levers (v2)
    # =========================================================

    def _evaluate_runnable(self):
        """
        Evaluate case runnability once and cache result.
        """

        if hasattr(self, "_runnable_cache"):
            return

        try:
            raw = self._raw_dict
            dirname = str(self.path.parent)

            plan = config_to_plan(
                raw,
                dirname=dirname,
                loadHFP=True,
                verbose=False,
                logstreams=[StringIO(), StringIO()],
            )

            plan.solve(plan.objective, plan.solverOptions)

            if getattr(plan, "caseStatus", None) == "solved":
                self._runnable_cache = True
                self._runnable_error = None
            else:
                self._runnable_cache = False
                self._runnable_error = "Solver did not return solved status."

        except Exception as e:
            self._runnable_cache = False
            self._runnable_error = str(e)

    @property
    def is_runnable(self) -> bool:
        self._evaluate_runnable()
        return self._runnable_cache

    @property
    def run_error(self) -> str | None:
        self._evaluate_runnable()
        return self._runnable_error

    @property
    def _lever_summary(self):
        """
        Lazy-compute solver-based levers.
        Cached per Case instance.
        """
        if not hasattr(self, "_lever_cache"):
            from owlroost.domain.services.levers import compute_levers

            self._lever_cache = compute_levers(self)
        return self._lever_cache

    @property
    def retirement_horizon(self) -> int | None:
        if not self._cache_is_valid():
            return None
        return self.cache.retirement_horizon

    @property
    def max_spending(self) -> float | None:
        if not self._cache_is_valid():
            return None
        return self.cache.max_spending

    @property
    def first_year_total_withdrawals(self) -> float | None:
        if not self._cache_is_valid():
            return None
        return self.cache.first_year_total_withdrawals

    @property
    def has_retirement_lever(self) -> bool:
        """
        Retirement lever exists if retirement occurs
        within the planning horizon and is not already retired.
        """
        horizon = self.retirement_horizon

        if horizon is None:
            return False  # never retires → no lever

        if horizon == 0:
            return False  # already retired → no lever

        return True

    # =========================================================
    # Structural Lever Properties (v1)
    # =========================================================

    @property
    def has_ss_lever(self) -> bool:
        """
        Social Security lever exists only if PIA > 0.
        """
        return any(pia > 0 for pia in self.social_security_pia)

    @property
    def has_conversion_lever(self) -> bool:
        """
        Conversion lever exists if pre-tax assets exist, since these can be converted to tax-free.
        """
        return self.tax_deferred_savings > 0

    @property
    def has_allocation_lever(self) -> bool:
        """
        Allocation lever exists if asset allocation is defined.
        """
        return bool(self.initial_asset_allocation)

    @property
    def pre_tax_share(self) -> float:
        """
        Share of total savings in tax-deferred accounts.
        """
        total = self.total_savings
        if total == 0:
            return 0.0
        return self.tax_deferred_savings / total

    @property
    def equity_share(self) -> float:
        """
        Equity share from first allocation vector.
        """
        allocs = self.initial_asset_allocation
        if not allocs:
            return 0.0

        first_alloc = allocs[0]
        if not first_alloc:
            return 0.0

        # First element corresponds to equities
        return first_alloc[0] / 100.0

    @property
    def funded_ratio(self) -> float:
        """
        Simple 25x rule funded ratio approximation.
        (Assets / 25x annual spending proxy)
        """

        spending = self.max_spending

        if not spending or spending <= 0:
            return 0.0

        return 1000.0 * self.total_savings / (25 * spending)

    @property
    def withdrawl_rate(self) -> float:
        """ """

        spending = self.first_year_total_withdrawals

        if not spending or spending <= 0:
            return 0.0

        return spending / (1000.0 * self.total_savings)
