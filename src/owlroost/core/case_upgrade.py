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

from owlroost.domain.case import Case, LongevityConfig, RoostConfig

# =========================================================
# Public API
# =========================================================


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
    # Persist if needed
    # ---------------------------------------------------------

    if write and any(
        actions[k]
        for k in (
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
    model = LongevityConfig(partnered=(len(case.household_names) == 2))
    model = case._align_longevity(model)

    case.extensions["longevity"] = model
    case.extra["longevity"] = model.model_dump(exclude_none=True)
    case._raw_dict["longevity"] = model.model_dump(exclude_none=True)


def _add_default_roost(case: Case) -> None:
    model = RoostConfig()
    case.extensions["roost"] = model
    case.extra["roost"] = model.model_dump(exclude_none=True)
    case._raw_dict["roost"] = model.model_dump(exclude_none=True)


def _align_longevity(case: Case) -> bool:
    """
    Re-align longevity lists to household size.
    Returns True if modification occurred.
    """

    lon = case.longevity
    if lon is None:
        return False

    n = len(case.household_names)

    aligned = _resize_longevity(lon, n)

    # Check if anything changed
    if aligned != lon:
        case.extensions["longevity"] = aligned
        case.extra["longevity"] = aligned.model_dump(exclude_none=True)
        case._raw_dict["longevity"] = aligned.model_dump(exclude_none=True)
        return True

    return False


def _resize_longevity(model: LongevityConfig, n: int) -> LongevityConfig:
    """
    Resize all longevity lists to match household size.
    """

    def resize(values: list, default):
        if len(values) < n:
            return values + [default] * (n - len(values))
        return values[:n]

    return LongevityConfig(
        apply_to_plan=model.apply_to_plan,
        life_expectancy_seed=model.life_expectancy_seed,
        partnered=(n == 2),
        lifetime_percentile=resize(model.lifetime_percentile, 0.50),
        sex=resize(model.sex, "female"),
        health=resize(model.health, "average"),
        smoker=resize(model.smoker, False),
    )
