# src/owlroost/schema/hydra_expanders.py

from __future__ import annotations

from owlroost.display.operations.normalize import (
    get_units_multiplier,
)

MARKET_REGIMES = {
    "full": (1928, 2025),
    "dotcom": (1994, 2000),
    "stagflation": (1966, 1982),
}


# =========================================================
# Registry
# =========================================================

EXPANDERS = []


def hydra_expander(fn):
    EXPANDERS.append(fn)
    return fn


# =========================================================
# Main
# =========================================================


def expand_hydra_helpers(
    run_dict,
):
    for fn in EXPANDERS:
        fn(run_dict)

    return run_dict


# =========================================================
# rates_selection.from_to
# =========================================================


@hydra_expander
def expand_rates_from_to(run_dict):
    rates = run_dict.setdefault(
        "rates_selection",
        {},
    )

    value = rates.pop(
        "from_to",
        None,
    )

    if not value:
        return

    start, end = value.split("-", 1)

    rates["from"] = int(start)
    rates["to"] = int(end)

    return run_dict


# =========================================================
# rates_selection.regime
# =========================================================


@hydra_expander
def expand_rates_regime(run_dict):
    rates = run_dict.setdefault(
        "rates_selection",
        {},
    )

    regime = rates.pop(
        "regime",
        None,
    )

    if not regime:
        return

    if regime not in MARKET_REGIMES:
        raise ValueError(f"Unknown regime: {regime}")

    start, end = MARKET_REGIMES[regime]

    rates["from"] = start
    rates["to"] = end

    return run_dict


# =========================================================
# fixed_income.ss_age_pair
# =========================================================


@hydra_expander
def expand_ss_age_pair(run_dict):
    fixed_income = run_dict.setdefault(
        "fixed_income",
        {},
    )

    value = fixed_income.pop(
        "ss_age_pair",
        None,
    )

    if not value:
        return

    p1, p2 = value.split("-", 1)

    fixed_income["social_security_age"] = [
        float(p1),
        float(p2),
    ]

    return run_dict


# =========================================================
# roost_runtime.optimization_goal
# =========================================================


@hydra_expander
def expand_optimization_goal(run_dict):
    """
    Expand semantic optimization goal helper.

    CLI values are ALWAYS interpreted as K-dollars,
    independent of solver_options.units.

    Examples:

        maxSpnd-0
        maxSpnd-250
        maxBeq-180
        maxBeq-1_250

    Meaning:

        maxSpnd-250
            -> bequest floor = $250K

        maxBeq-180
            -> net spending target = $180K

    Values are converted into the appropriate
    OWL-scaled units before persistence.
    """

    runtime = run_dict.setdefault(
        "roost_runtime",
        {},
    )

    value = runtime.pop(
        "optimization_goal",
        None,
    )

    if not value:
        return run_dict

    # -----------------------------------------------------
    # Parse helper
    # -----------------------------------------------------

    try:
        objective_name, target = value.split("-", 1)

    except Exception as exc:
        raise ValueError("Invalid roost_runtime.optimization_goal " f"value: {value}") from exc

    optimization = run_dict.setdefault(
        "optimization_parameters",
        {},
    )

    solver = run_dict.setdefault(
        "solver_options",
        {},
    )

    # -----------------------------------------------------
    # Parse CLI target (always K-dollars)
    # -----------------------------------------------------

    try:
        target_k_dollars = float(target.replace("_", ""))

    except Exception as exc:
        raise ValueError("Invalid optimization target " f"value: {target}") from exc

    # -----------------------------------------------------
    # Convert K-dollars -> configured OWL units
    # -----------------------------------------------------

    units = solver.get(
        "units",
        "k",
    )

    units_multiplier = get_units_multiplier(
        units,
    )

    # CLI is ALWAYS K-dollars
    #
    # Example:
    #   180 -> $180,000
    #
    # Convert into configured solver units.
    #
    # Examples:
    #
    # units="k"
    #   180 -> 180
    #
    # units="1"
    #   180 -> 180000
    #
    # units="M"
    #   180 -> 0.18
    # -----------------------------------------------------

    target_value = (target_k_dollars * 1_000.0) / units_multiplier

    # -----------------------------------------------------
    # Max Spending
    #
    # Example:
    #   maxSpnd-250
    #
    # Expands into:
    #   objective=maxSpending
    #   bequest=<scaled value>
    #
    # Removes:
    #   netSpending
    # -----------------------------------------------------

    if objective_name == "maxSpnd":
        optimization["objective"] = "maxSpending"

        solver["bequest"] = target_value

        # ---------------------------------------------
        # Remove conflicting constraint
        # ---------------------------------------------

        solver.pop(
            "netSpending",
            None,
        )

        return run_dict

    # -----------------------------------------------------
    # Max Bequest
    #
    # Example:
    #   maxBeq-180
    #
    # Expands into:
    #   objective=maxBequest
    #   netSpending=<scaled value>
    #
    # Removes:
    #   bequest
    # -----------------------------------------------------

    if objective_name == "maxBeq":
        optimization["objective"] = "maxBequest"

        solver["netSpending"] = target_value

        # ---------------------------------------------
        # Remove conflicting constraint
        # ---------------------------------------------

        solver.pop(
            "bequest",
            None,
        )

        return run_dict

    # -----------------------------------------------------
    # Unknown objective
    # -----------------------------------------------------

    raise ValueError("Unknown optimization objective " f"in optimization_goal: {objective_name}")
