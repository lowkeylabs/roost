from __future__ import annotations

from typing import Any

from owlroost.domain.models.case import (
    Case,
    LongevityConfig,
    RoostConfig,
    SpendingPolicyConfig,
)

# =========================================================
# Public API
# =========================================================


def case_upgrade(
    case: Case,
    *,
    write: bool = False,
    verbose: bool = False,
) -> dict[str, Any]:
    actions: dict[str, Any] = {
        "spending_policy_added": False,
        "spending_policy_updated": False,
        "longevity_added": False,
        "roost_added": False,
        "longevity_fixed_alignment": False,
        "life_expectancy_updated": False,
        "written": False,
        "runtime_environment_added": False,
    }

    # ---------------------------------------------------------
    # Longevity
    # ---------------------------------------------------------

    if case.longevity is None:
        _add_default_longevity(case)
        actions["longevity_added"] = True
        if verbose:
            print("Added default [longevity] section.")
    else:
        if _align_longevity(case):
            actions["longevity_fixed_alignment"] = True
            if verbose:
                print("Aligned longevity section with household.")

    # ---------------------------------------------------------
    # Apply Longevity
    # ---------------------------------------------------------

    if case.longevity and case.longevity.apply_to_plan:
        deterministic = case.deterministic_life_ages

        if deterministic:
            rounded = [int(round(age)) for age in deterministic]

            current = case.config.basic_info.life_expectancy

            if current != rounded:
                case.config.basic_info.life_expectancy = rounded
                case._raw_dict["basic_info"]["life_expectancy"] = rounded
                actions["life_expectancy_updated"] = True

                if verbose:
                    print("Applied deterministic longevity to plan.")

    # ---------------------------------------------------------
    # Roost
    # ---------------------------------------------------------

    if case.roost is None:
        _add_default_roost(case)
        actions["roost_added"] = True
        if verbose:
            print("Added default [roost] section.")

    # ---------------------------------------------------------
    # Runtime Environment
    # ---------------------------------------------------------

    if "runtime_environment" not in case._raw_dict:
        _add_default_runtime_environment(case)
        actions["runtime_environment_added"] = True
        if verbose:
            print("Added default [runtime_environment] section.")

    # Always mirror into case.extra
    if "runtime_environment" in case._raw_dict:
        case.extra["runtime_environment"] = case._raw_dict["runtime_environment"]

    # ---------------------------------------------------------
    # Spending Policy (STRICT NEW SCHEMA)
    # ---------------------------------------------------------

    if case.spending_policy is None:
        _add_default_spending_policy(case)
        actions["spending_policy_added"] = True
        if verbose:
            print("Added default [spending_policy] section.")
    else:
        policy = case.spending_policy
        updated = False

        # -----------------------------------------------------
        # Validate required fields
        # -----------------------------------------------------

        if policy.essential_spending is None:
            raise ValueError("essential_spending must be provided in [spending_policy]")

        if policy.lifestyle_spending is None:
            raise ValueError("lifestyle_spending must be provided in [spending_policy]")

        # -----------------------------------------------------
        # Validate numeric
        # -----------------------------------------------------

        if isinstance(policy.essential_spending, str):
            raise ValueError("essential_spending must be numeric")

        if isinstance(policy.lifestyle_spending, str):
            raise ValueError("lifestyle_spending must be numeric")

        # -----------------------------------------------------
        # Enforce constraint
        # -----------------------------------------------------

        if policy.lifestyle_spending < policy.essential_spending:
            policy.lifestyle_spending = policy.essential_spending
            updated = True

            if verbose:
                print("Adjusted lifestyle_spending to match essential_spending")

        # -----------------------------------------------------
        # Persist canonical structure
        # -----------------------------------------------------

        sp = case.extra.setdefault("spending_policy", {})
        raw_sp = case._raw_dict.setdefault("spending_policy", {})

        sp["essential_spending"] = policy.essential_spending
        sp["lifestyle_spending"] = policy.lifestyle_spending

        raw_sp["essential_spending"] = policy.essential_spending
        raw_sp["lifestyle_spending"] = policy.lifestyle_spending

        # Preserve additional fields
        for k in (
            "baseline_years",
            "max_years_below_threshhold",
            "max_consecutive_years_below_threshhold",
        ):
            v = getattr(policy, k, None)
            if v is not None:
                sp[k] = v
                raw_sp[k] = v

        if updated:
            actions["spending_policy_updated"] = True

    # ---------------------------------------------------------
    # Persist
    # ---------------------------------------------------------

    if write and any(
        actions[k]
        for k in (
            "spending_policy_added",
            "spending_policy_updated",
            "longevity_added",
            "roost_added",
            "longevity_fixed_alignment",
            "life_expectancy_updated",
            "runtime_environment_added",
        )
    ):
        case.write()
        actions["written"] = True
        if verbose:
            print(f"Case written to disk: {case.path}")

    return actions


# =========================================================
# Helpers
# =========================================================


def _add_default_longevity(case: Case) -> None:
    model = LongevityConfig(partnered=(len(case.household_names) == 2))
    model = model.resized(len(case.household_names))

    case.extensions["longevity"] = model
    case.extra["longevity"] = model.model_dump(exclude_none=True, by_alias=True)
    case._raw_dict["longevity"] = model.model_dump(exclude_none=True, by_alias=True)


def _add_default_roost(case: Case) -> None:
    model = RoostConfig()
    case.extensions["roost"] = model
    case.extra["roost"] = model.model_dump(exclude_none=True, by_alias=True)
    case._raw_dict["roost"] = model.model_dump(exclude_none=True, by_alias=True)


def _add_default_runtime_environment(case: Case) -> None:
    env = {
        # Prevent oversubscription across ROOST parallel trials
        "OMP_NUM_THREADS": 1,
        "MKL_NUM_THREADS": 1,
        "OPENBLAS_NUM_THREADS": 1,
        # MOSEK-specific settings
        "MSK_IPAR_NUM_THREADS": 1,
        # "MOSEK_SYS_NUM_CORES" : 1,
    }

    case._raw_dict["runtime_environment"] = env
    case.extra["runtime_environment"] = env


def _add_default_spending_policy(case: Case) -> None:
    model = SpendingPolicyConfig(
        essential_spending=0,
        lifestyle_spending=0,
    )

    case.extensions["spending_policy"] = model
    case.extra["spending_policy"] = model.model_dump(exclude_none=True, by_alias=True)
    case._raw_dict["spending_policy"] = model.model_dump(exclude_none=True, by_alias=True)


def _align_longevity(case: Case) -> bool:
    lon = case.longevity
    if lon is None:
        return False

    n = len(case.household_names)
    aligned = lon.resized(n)

    if aligned != lon:
        case.extensions["longevity"] = aligned
        case.extra["longevity"] = aligned.model_dump(exclude_none=True, by_alias=True)
        case._raw_dict["longevity"] = aligned.model_dump(exclude_none=True, by_alias=True)
        return True

    return False
