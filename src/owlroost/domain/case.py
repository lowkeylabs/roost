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
    def taxable_assets(self) -> float:
        return sum(self.config.savings_assets.taxable_savings_balances)

    @property
    def tax_deferred_assets(self) -> float:
        return sum(self.config.savings_assets.tax_deferred_savings_balances)

    @property
    def tax_free_assets(self) -> float:
        return sum(self.config.savings_assets.tax_free_savings_balances)

    @property
    def total_assets(self) -> float:
        return self.taxable_assets + self.tax_deferred_assets + self.tax_free_assets

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
