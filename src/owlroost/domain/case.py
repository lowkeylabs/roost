from datetime import date
from pathlib import Path

from owlplanner.config.schema import config_dict_to_model
from owlplanner.config.toml_io import load_toml


class Case:
    """
    Domain wrapper around CaseConfig.

    This object exists for:
    - Calculated attributes
    - Display normalization
    - Future expansion
    """

    def __init__(self, path: Path):
        self.path = path
        self._raw_dict, _, _ = load_toml(str(path))
        self.config, self.extra = config_dict_to_model(self._raw_dict)

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

        # Assume ISO string
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
        """
        Current ages at start_date (approximate, year-based).
        """
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
    # Asset Allocation (initial structural input)
    # ---------------------------------------------------------

    @property
    def initial_asset_allocation(self) -> list[list[int]]:
        """
        Returns initial allocation per individual at start year.
        Extracts first regime allocation from asset_allocation.generic.
        """

        alloc = self.config.asset_allocation

        if not alloc or not getattr(alloc, "generic", None):
            return []

        generic = alloc.generic

        result = []

        for person in generic:
            if not person:
                continue
            # take first regime block
            result.append(person[0])

        return result

    @property
    def allocation_sentence(self) -> str:
        allocs = self.initial_asset_allocation

        if not allocs:
            return ""

        # If all persons identical, describe once
        if all(a == allocs[0] for a in allocs):
            alloc = allocs[0]
            return self._allocation_vector_to_sentence(alloc)

        # Otherwise describe per person
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

        # If two components
        if len(components) == 2:
            (p1, l1), (p2, l2) = components
            return f"{p1}% {l1} and {p2}% {l2}"

        # Three or four components
        parts = [f"{pct}% {label}" for pct, label in components]
        return ", ".join(parts[:-1]) + f", and {parts[-1]}"

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
