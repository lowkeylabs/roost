# src/owlroost/schema/runtime_defaults.py

from io import StringIO

from owlplanner.config.plan_bridge import config_to_plan, plan_to_config


def _get_safe_rate_range():
    """
    Determine a valid (from, to) range for OWL rates.

    We avoid hardcoding by using a conservative default window
    known to be valid for all OWL datasets (1928–present).
    """

    # These bounds are guaranteed valid per OWL spec
    # (1928–2025 currently)
    start = 1960
    end = 2020

    return start, end


def build_runtime_defaults():
    """
    Build canonical default config using OWL.

    Returns:
        dict: full default config
    """

    rate_from, rate_to = _get_safe_rate_range()

    # minimal VALID config seed (must satisfy OWL loader)
    seed = {
        "case_name": "default",
        "description": "this is a default case.",
        "basic_info": {
            "status": "single",
            "names": ["A"],
            "sexes": ["M"],
            "date_of_birth": ["1960-01-01"],
            "life_expectancy": [90],
            "start_date": "2026-01-01",
        },
        "savings_assets": {
            "taxable_savings_balances": [0],
            "tax_deferred_savings_balances": [0],
            "tax_free_savings_balances": [0],
            "hsa_savings_balances": [0],
            "beneficiary_fractions": [1.0, 1.0, 1.0, 1.0],
            "spousal_surplus_deposit_fraction": 0.5,
        },
        "fixed_income": {
            "pension_monthly_amounts": [0],
            "pension_ages": [65],
            "pension_indexed": [False],
            "pension_survivor_fraction": [0],
            "social_security_pia_amounts": [0],
            "social_security_ages": [67],
        },
        "rates_selection": {
            "method": "historical average",
            "from": 1960,
            "to": 2020,
        },
        "asset_allocation": {
            "type": "individual",
            "interpolation_method": "linear",
            "interpolation_center": 15,
            "interpolation_width": 5,
            "generic": [
                [
                    [60, 40, 0, 0],
                    [60, 40, 0, 0],
                ]
            ],
        },
        "optimization_parameters": {
            "objective": "maxSpending",
            "spending_profile": "flat",
            "surviving_spouse_spending_percent": 60,
        },
        "solver_options": {
            "bequest": 0,
            "solver": "default",
            "withMedicare": "loop",
            "withSSTaxability": "loop",
            "withSCLoop": True,
            "startRothConversions": 2026,
        },
        "roost": {},
    }

    # toss logstreams when building defaults
    logstreams = [StringIO(), StringIO()]
    plan = config_to_plan(seed, loadHFP=False, logstreams=logstreams)
    defaults = plan_to_config(plan)

    defaults.setdefault("case_name", "default")

    return defaults


def get_from_path(d: dict, path: tuple[str, ...]):
    cur = d
    for p in path:
        if not isinstance(cur, dict):
            return None
        if p not in cur:
            return None
        cur = cur[p]
    return cur
