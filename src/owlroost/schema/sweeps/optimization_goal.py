# src/owlroost/schema/sweeps/optimization_goal.py

"""
roost_sweeps.optimization_goal sweep variable.

Notes
-----
Provides a high-level optimization sweep
dimension that expands into the underlying
OWL optimization configuration.

Examples
--------

    maxSpnd-250

expands to:

    objective=maxSpending
    bequest=250

and:

    maxBeq-180

expands to:

    objective=maxBequest
    netSpending=180

CLI values are always interpreted as
K-dollars regardless of configured
OWL solver units.
"""

from __future__ import annotations

from owlroost.catalog.ontology import (
    CatalogNodeType,
)
from owlroost.display.operations.normalize import (
    get_units_multiplier,
)

from ..registry import (
    FieldSpec,
)

# =========================================================
# Registration
# =========================================================


def register_schema_fields(
    reg,
):
    """
    Register optimization goal sweep field.
    """

    reg.register(
        FieldSpec(
            # =================================================
            # Identity
            # =================================================
            name=("roost_sweeps.optimization_goal"),
            dtype=str,
            # =================================================
            # Runtime Realization
            # =================================================
            path=(
                "roost_sweeps",
                "optimization_goal",
            ),
            source="sweep",
            # =================================================
            # Ontology
            # =================================================
            owner="ROOST",
            semantic_domain="decision",
            value_origin="user-specified",
            projection_kind="canonical",
            analytic_kind="observed",
            materialization_level="run",
            node_type=(CatalogNodeType.VARIABLE),
            expands_to=[
                ("optimization_parameters.objective"),
                "solver_options.bequest",
                ("solver_options.netSpending"),
            ],
            # =================================================
            # Documentation
            # =================================================
            description=("Semantic optimization goal sweep variable."),
            defined_in=("optimization_goal"),
        )
    )


# =========================================================
# Expansion
# =========================================================


def expand(
    run_dict,
):
    """
    Expand semantic optimization goal.

    CLI values are ALWAYS interpreted
    as K-dollars regardless of the
    configured OWL solver units.

    Examples
    --------

        maxSpnd-250

    expands to:

        objective=maxSpending
        bequest=250K

    and:

        maxBeq-180

    expands to:

        objective=maxBequest
        netSpending=180K
    """

    runtime = run_dict.setdefault(
        "roost_sweeps",
        {},
    )

    value = runtime.pop(
        "optimization_goal",
        None,
    )

    if not value:
        return run_dict

    # =====================================================
    # Parse helper
    # =====================================================

    try:
        objective_name, target = value.split(
            "-",
            1,
        )

    except Exception as err:
        raise ValueError(f"Invalid roost_sweeps.optimization_goal value: {value}") from err

    optimization = run_dict.setdefault(
        "optimization_parameters",
        {},
    )

    solver = run_dict.setdefault(
        "solver_options",
        {},
    )

    # =====================================================
    # Parse target
    # =====================================================

    try:
        target_k_dollars = float(
            target.replace(
                "_",
                "",
            )
        )

    except Exception as err:
        raise ValueError(f"Invalid optimization target value: {target}") from err

    # =====================================================
    # Convert K-dollars into configured
    # OWL solver units
    # =====================================================

    units = solver.get(
        "units",
        "k",
    )

    units_multiplier = get_units_multiplier(
        units,
    )

    target_value = target_k_dollars * 1_000.0 / units_multiplier

    # =====================================================
    # Max Spending
    # =====================================================

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

    # =====================================================
    # Max Bequest
    # =====================================================

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

    # =====================================================
    # Unknown Objective
    # =====================================================

    raise ValueError(f"Unknown optimization objective in optimization_goal: {objective_name}")
