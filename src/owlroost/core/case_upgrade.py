"""
Case upgrade workflow for ROOST.

Responsible for:

- Ensuring required ROOST extension sections exist
- Injecting default [longevity] and [roost] sections when missing
- Validating structural alignment with household size
- Writing back to disk if requested

This module intentionally contains orchestration logic.
The Case class remains a passive domain model.
"""

from __future__ import annotations

from typing import Dict, Any

from owlroost.domain.case import Case, LongevityConfig, RoostConfig

# =========================================================
# Public API
# =========================================================


def case_upgrade(
    case: Case,
    *,
    write: bool = False,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Upgrade a Case to ensure ROOST compatibility.

    Args:
        case: Case instance
        write: If True, write modifications to disk
        verbose: If True, include detailed messages

    Returns:
        dict containing actions taken
    """

    actions: Dict[str, Any] = {
        "longevity_added": False,
        "roost_added": False,
        "longevity_fixed_alignment": False,
        "written": False,
    }

    # ---------------------------------------------------------
    # Ensure Longevity Section
    # ---------------------------------------------------------

    if case.longevity is None:
        _add_default_longevity(case)
        actions["longevity_added"] = True
        if verbose:
            print("Added default [longevity] section.")

    else:
        if _fix_longevity_alignment(case):
            actions["longevity_fixed_alignment"] = True
            if verbose:
                print("Fixed longevity section alignment.")

    # ---------------------------------------------------------
    # Ensure Roost Section
    # ---------------------------------------------------------

    if case.roost is None:
        _add_default_roost(case)
        actions["roost_added"] = True
        if verbose:
            print("Added default [roost] section.")

    # ---------------------------------------------------------
    # Write Back If Needed
    # ---------------------------------------------------------

    if write and any(
        actions[k]
        for k in ("longevity_added", "roost_added", "longevity_fixed_alignment")
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
    Create a default [longevity] section based on household size.
    """

    n = len(case.household_names)

    default_section = {
        "apply_to_plan": False,
        "life_expectancy_seed": None,
        "partnered": n == 2,
        "survival_percentile": [0.50] * n,
        "sex": ["female"] * n,
        "health": ["average"] * n,
        "smoker": [False] * n,
    }

    case.extra["longevity"] = default_section
    case.extensions["longevity"] = LongevityConfig(**default_section)


def _add_default_roost(case: Case) -> None:
    """
    Create a default [roost] section.
    """

    default_section = {
        "use_bootstrap_model": False,
        "master_seed": None,
        "trials": 1,
    }

    case.extra["roost"] = default_section
    case.extensions["roost"] = RoostConfig(**default_section)


def _fix_longevity_alignment(case: Case) -> bool:
    """
    Ensure longevity list lengths match household size.
    """

    lon = case.longevity
    if lon is None:
        return False

    n = len(case.household_names)
    modified = False

    survival_percentile = list(lon.survival_percentile)
    sex = list(lon.sex)
    health = list(lon.health)
    smoker = list(lon.smoker)

    if len(survival_percentile) != n:
        survival_percentile = _resize_list(
            survival_percentile, n, 0.50
        )
        modified = True

    if len(sex) != n:
        sex = _resize_list(sex, n, "female")
        modified = True

    if len(health) != n:
        health = _resize_list(health, n, "average")
        modified = True

    if len(smoker) != n:
        smoker = _resize_list(smoker, n, False)
        modified = True

    if modified:
        updated = {
            "apply_to_plan": lon.apply_to_plan,
            "life_expectancy_seed": lon.life_expectancy_seed,
            "partnered": n == 2,
            "survival_percentile": survival_percentile,
            "sex": sex,
            "health": health,
            "smoker": smoker,
        }

        case.extra["longevity"] = updated
        case.extensions["longevity"] = LongevityConfig(**updated)

    return modified

def _resize_list(values: list, n: int, default):
    """
    Resize list to length n.
    If too short, extend with default.
    If too long, truncate.
    """
    if len(values) < n:
        return values + [default] * (n - len(values))
    return values[:n]


# ============================================================
# Deterministic percentile inversion
# ============================================================


def gm_percentile_age(
    current_age: float,
    A: float,
    B: float,
    C: float,
    survival_percentile: float,
    max_age: int = 120,
) -> float:
    """
    Deterministically compute the age A such that:

        P(alive at A | alive at current_age) = survival_percentile

    Uses integer-age grid consistent with annual planning model.
    """

    if not (0.0 < survival_percentile <= 1.0):
        raise ValueError("survival_percentile must be in (0, 1].")

    ages = np.arange(current_age, max_age + 1, 1.0)

    S = survival_function(ages, A, B, C)
    S0 = survival_function(current_age, A, B, C)

    S_cond = S / S0  # conditional survival

    # Survival is decreasing. We invert it.
    # Reverse arrays so we can use interpolation safely.
    return float(
        np.interp(
            survival_percentile,
            S_cond[::-1],
            ages[::-1],
        )
    )

def deterministic_individual_lifetime(
    current_age: float,
    survival_percentile: float,
    health: str = "average",
    sex: str = "female",
    smoker: bool = False,
    partnered: bool = False,
) -> float:
    """
    Compute deterministic lifespan at given survival percentile.
    """

    A, B, C = adjust_parameters(health, current_age, sex, smoker, partnered)

    return gm_percentile_age(
        current_age=current_age,
        A=A,
        B=B,
        C=C,
        survival_percentile=survival_percentile,
    )

def deterministic_lifetime_pair(
    age1: float,
    age2: float,
    survival_percentile,
    health1: str = "average",
    health2: str = "average",
    sex1: str = "female",
    sex2: str = "male",
    smoker1: bool = False,
    smoker2: bool = False,
    partnered: bool = True,
):
    """
    Deterministically compute lifetimes for a pair.

    survival_percentile may be:
        - scalar → applied to both
        - list/tuple of length 2 → individual percentiles

    Returns:
        (life1_age, life2_age, last_survivor_age)
    """

    if isinstance(survival_percentile, (list, tuple)):
        if len(survival_percentile) != 2:
            raise ValueError(
                "survival_percentile list must have length 2 for paired case."
            )
        p1, p2 = survival_percentile
    else:
        p1 = p2 = survival_percentile

    life1 = deterministic_individual_lifetime(
        current_age=age1,
        survival_percentile=p1,
        health=health1,
        sex=sex1,
        smoker=smoker1,
        partnered=partnered,
    )

    life2 = deterministic_individual_lifetime(
        current_age=age2,
        survival_percentile=p2,
        health=health2,
        sex=sex2,
        smoker=smoker2,
        partnered=partnered,
    )

    return life1, life2, max(life1, life2)

