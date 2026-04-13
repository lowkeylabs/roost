"""
Case upgrade workflow for ROOST.

Responsible for:

- Ensuring required ROOST extension sections exist
- Injecting default [longevity] and [roost] sections when missing
- Validating structural alignment with household size
- Applying deterministic longevity to plan (if requested)
- Writing back to disk if requested

Defaults are defined in schema models.
"""

from __future__ import annotations

from typing import Any

from owlroost.domain.models.case import Case, LongevityConfig, RoostConfig, SpendingPolicyConfig

# =========================================================
# Public API
# =========================================================


def _default_minimum_spending(case: Case) -> float:
    """
    Compute a reasonable default minimum spending based on household size.
    """
    n = len(case.household_names)
    return 50 + 30 * (n - 1)


def case_upgrade(
    case: Case,
    *,
    write: bool = False,
    verbose: bool = False,
) -> dict[str, Any]:
    """
    Upgrade a Case to ensure ROOST compatibility.
    """

    actions: dict[str, Any] = {
        "spending_policy_added": False,
        "spending_policy_updated": False,
        "longevity_added": False,
        "roost_added": False,
        "longevity_fixed_alignment": False,
        "life_expectancy_updated": False,
        "written": False,
    }

    # ---------------------------------------------------------
    # Longevity Section
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
    # Apply Longevity to Plan (if requested)
    # ---------------------------------------------------------

    if case.longevity and case.longevity.apply_to_plan:
        deterministic = case.deterministic_life_ages

        if deterministic:
            # Round to nearest integer age
            rounded = [int(round(age)) for age in deterministic]

            current = case.config.basic_info.life_expectancy

            if current != rounded:
                case.config.basic_info.life_expectancy = rounded
                case._raw_dict["basic_info"]["life_expectancy"] = rounded
                actions["life_expectancy_updated"] = True

                if verbose:
                    print("Applied deterministic longevity to plan.")

    # ---------------------------------------------------------
    # Roost Section
    # ---------------------------------------------------------

    if case.roost is None:
        _add_default_roost(case)
        actions["roost_added"] = True
        if verbose:
            print("Added default [roost] section.")

    # ---------------------------------------------------------
    # Spending policy section
    # ---------------------------------------------------------

    if case.spending_policy is None:
        _add_default_spending_policy(case)
        actions["spending_policy_added"] = True
        if verbose:
            print("Added default [spending_policy] section.")
    else:
        policy = case.spending_policy

        if isinstance(policy.minimum_spending, str):
            raise ValueError("minimum_spending must be a fixed numeric value, not a percentage")

        if policy.minimum_spending is None:
            default_val = _default_minimum_spending(case)
            policy.minimum_spending = default_val

            if "spending_policy" not in case.extra:
                case.extra["spending_policy"] = {}

            case.extra["spending_policy"]["minimum_spending"] = default_val
            case._raw_dict["spending_policy"]["minimum_spending"] = default_val

            actions["spending_policy_updated"] = True

            if verbose:
                print(
                    f"Injected default minimum_spending = ${default_val:,.0f} (household size = {len(case.household_names)})"
                )

    # ---------------------------------------------------------
    # Persist if needed
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
        )
    ):
        case.write()
        actions["written"] = True
        if verbose:
            print(f"Case written to disk: {case.path}")

    return actions


# =========================================================
# Internal Helpers
# =========================================================


def _add_default_longevity(case: Case) -> None:
    """
    Inject default longevity section using schema defaults,
    then resize via LongevityConfig.resized().
    """
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


def _add_default_spending_policy(case: Case) -> None:
    model = SpendingPolicyConfig()

    if model.minimum_spending is None:
        model.minimum_spending = _default_minimum_spending(case)

    case.extensions["spending_policy"] = model
    case.extra["spending_policy"] = model.model_dump(exclude_none=True, by_alias=True)
    case._raw_dict["spending_policy"] = model.model_dump(exclude_none=True, by_alias=True)


def _align_longevity(case: Case) -> bool:
    """
    Re-align longevity lists to household size using
    LongevityConfig.resized().

    Returns True if modification occurred.
    """

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
