import ast
import re
import secrets
from datetime import date
from pathlib import Path
from typing import Any

from owlplanner.config.schema import config_dict_to_model
from owlplanner.config.toml_io import load_toml, save_toml
from pydantic import BaseModel, Field, field_validator

from owlroost.core.longevity import deterministic_individual_lifetime

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


EXTRA_SECTION_REGISTRY: dict[str, type[BaseModel]] = {
    "longevity": LongevityConfig,
    "roost": RoostConfig,
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
            core_dict = self.config.model_dump()
        else:
            core_dict = self.config.dict()

        updated = dict(self._raw_dict)

        for k, v in core_dict.items():
            updated[k] = v

        for name, model in self.extensions.items():
            updated[name] = model.model_dump(exclude_none=True)

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

    def write(self, path: Path | None = None) -> None:
        target_path = Path(path or self.path)
        filename = target_path.name

        if filename.lower().startswith("case_"):
            final_path = str(target_path)
        else:
            final_path = str(target_path.with_name(f"case_{filename}"))

        for name, model in self.extensions.items():
            self.extra[name] = model.model_dump(exclude_none=True)

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
            life_expectancy_seed=model.life_expectancy_seed,
            partnered=(n == 2),
            lifetime_percentile=self._resize_list(model.lifetime_percentile, n, 0.60),
            sex=self._resize_list(model.sex, n, "female"),
            health=self._resize_list(model.health, n, "average"),
            smoker=self._resize_list(model.smoker, n, False),
        )

    @staticmethod
    def _resize_list(values: list, n: int, default):
        if len(values) < n:
            return values + [default] * (n - len(values))
        return values[:n]

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
            deterministic_individual_lifetime(
                current_age=current_ages[i],
                lifetime_percentile=lon.lifetime_percentile[i],
                health=lon.health[i],
                sex=lon.sex[i],
                smoker=lon.smoker[i],
                partnered=lon.partnered,
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
