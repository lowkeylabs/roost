import secrets
from datetime import date
from pathlib import Path

from owlplanner.config.schema import config_dict_to_model
from owlplanner.config.toml_io import load_toml, save_toml
from pydantic import BaseModel, Field, ValidationError, field_validator

from owlroost.core.longevity import (
    deterministic_individual_lifetime,
)

# =========================================================
# ROOST Extension Schemas
# =========================================================


class LongevityConfig(BaseModel):
    apply_to_plan: bool = False
    life_expectancy_seed: int | None = None

    partnered: bool = True

    lifetime_percentile: list[float] = Field(default_factory=lambda: [0.60])
    sex: list[str] = Field(default_factory=lambda: ["female"])
    health: list[str] = Field(default_factory=lambda: ["average"])
    smoker: list[bool] = Field(default_factory=lambda: [False])

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


class RoostConfig(BaseModel):
    master_seed: int = Field(default_factory=lambda: secrets.randbits(32))
    trials: int = 1000


# Registry of supported extra sections
EXTRA_SECTION_REGISTRY: dict[str, type[BaseModel]] = {
    "longevity": LongevityConfig,
    "roost": RoostConfig,
}


# =========================================================
# Case
# =========================================================


class Case:
    """
    Domain wrapper around CaseConfig.

    This object exists for:
    - Calculated attributes
    - Display normalization
    - Future expansion

    Supports ROOST extension sections via self.extra:
      - [longevity]
      - [roost]
    """

    def __init__(self, path: Path):
        self.path = path
        self._raw_dict, _, _ = load_toml(str(path))
        self.config, self.extra = config_dict_to_model(self._raw_dict)

        # -----------------------------------------------------
        # Extension Loading (from OWL self.extra)
        # -----------------------------------------------------

        self.extensions: dict[str, BaseModel] = {}

        for section_name, schema in EXTRA_SECTION_REGISTRY.items():
            section_data = self.extra.get(section_name)
            if section_data is not None:
                try:
                    model = schema(**section_data)

                    # Longevity requires household alignment
                    if section_name == "longevity":
                        model = self._align_longevity(model)

                    self.extensions[section_name] = model

                except ValidationError as e:
                    raise ValueError(
                        f"Invalid [{section_name}] section in {self.path.name}: {e}"
                    ) from e

    # ---------------------------------------------------------
    # Persistence
    # ---------------------------------------------------------

    def write(self, path: Path | None = None) -> None:
        """
        Write case back to disk, preserving OWL sections and
        updating ROOST extension sections.
        """

        target_path = Path(path or self.path)
        filename = target_path.name

        # Accept both case_ and Case_
        if filename.lower().startswith("case_"):
            final_path = str(target_path)
        else:
            final_path = str(target_path.with_name(f"case_{filename}"))

        # Sync extensions back into self.extra
        for name, model in self.extensions.items():
            self.extra[name] = model.model_dump(exclude_none=True)

        # Merge extra into original raw dict
        updated_dict = dict(self._raw_dict)

        for name, section in self.extra.items():
            updated_dict[name] = section

        # Use OWL save function
        save_toml(updated_dict, final_path)

    # ---------------------------------------------------------
    # Longevity Alignment
    # ---------------------------------------------------------

    def _align_longevity(self, model: LongevityConfig) -> LongevityConfig:
        """
        Ensure longevity lists match household size.
        """

        n = len(self.household_names)

        lifetime_percentile = self._resize_list(model.lifetime_percentile, n, 0.60)
        sex = self._resize_list(model.sex, n, "female")
        health = self._resize_list(model.health, n, "average")
        smoker = self._resize_list(model.smoker, n, False)

        return LongevityConfig(
            apply_to_plan=model.apply_to_plan,
            life_expectancy_seed=model.life_expectancy_seed,
            partnered=(n == 2),
            lifetime_percentile=lifetime_percentile,
            sex=sex,
            health=health,
            smoker=smoker,
        )

    @staticmethod
    def _resize_list(values: list, n: int, default):
        if len(values) < n:
            return values + [default] * (n - len(values))
        return values[:n]

    # ---------------------------------------------------------
    # Extension Accessors
    # ---------------------------------------------------------

    @property
    def longevity(self) -> LongevityConfig | None:
        return self.extensions.get("longevity")

    @property
    def roost(self) -> RoostConfig | None:
        return self.extensions.get("roost")

    @property
    def has_longevity_section(self) -> bool:
        return "longevity" in self.extra

    # ---------------------------------------------------------
    # Basic properties
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Assets (computed)
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Optimization
    # ---------------------------------------------------------

    @property
    def objective(self) -> str:
        return self.config.optimization_parameters.objective

    @property
    def spending_profile(self) -> str:
        return self.config.optimization_parameters.spending_profile

    # ---------------------------------------------------------
    # Ages
    # ---------------------------------------------------------

    @property
    def ages(self) -> list[int]:
        dobs = self.config.basic_info.date_of_birth
        if not dobs:
            return []

        start_year = int(self.start_date.split("-")[0])
        ages = []

        for dob in dobs:
            birth_year = int(dob.split("-")[0])
            ages.append(start_year - birth_year)

        return ages

    @property
    def life_expectancies(self) -> list[int]:
        return self.config.basic_info.life_expectancy

    @property
    def deterministic_life_ages(self) -> list[float]:
        """
        Deterministic life ages derived from the longevity section
        using percentile-based inversion of the Gompertz–Makeham model.

        Returns empty list if longevity section is absent.
        """

        if self.longevity is None:
            return []

        lon = self.longevity
        current_ages = self.ages

        results: list[float] = []

        for i in range(len(current_ages)):
            life_age = deterministic_individual_lifetime(
                current_age=current_ages[i],
                lifetime_percentile=lon.lifetime_percentile[i],
                health=lon.health[i],
                sex=lon.sex[i],
                smoker=lon.smoker[i],
                partnered=lon.partnered,
            )
            results.append(life_age)

        return results

    @property
    def deterministic_last_survivor_age(self) -> float | None:
        """
        Deterministic last-survivor age for partnered households.
        """

        ages = self.deterministic_life_ages

        if not ages:
            return None

        return max(ages)

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

    # ---------------------------------------------------------
    # Fixed income summary
    # ---------------------------------------------------------

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
