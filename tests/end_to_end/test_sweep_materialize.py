from __future__ import annotations


def test_materialize_ss_age_pair(
    build_session,
    load_run_plan,
    load_trial_toml,
):
    """
    Verify ss_age_pair materialization
    survives the entire BUILD pipeline.
    """

    session = build_session(
        "case_alex+jamie.toml",
        "roost_sweeps.ss_age_pair=69.11-69.22",
        "roost_settings.trials_per_run=10",
        "rates_selection.method=historical_bootstrap",
    )

    # -------------------------------------------------
    # Verify materialized run through OWL
    # -------------------------------------------------

    plan = load_run_plan(
        session,
        run_id=0,
    )

    assert plan.ssecAges.tolist() == [
        69.11,
        69.22,
    ]


def test_materialize_regime(
    build_session,
    load_run_plan,
    load_trial_toml,
):
    """
    Verify regime sweep materialization
    survives the entire BUILD pipeline.
    """

    regime = "stagflation"

    session = build_session(
        "case_alex+jamie.toml",
        "rates_selection.method=bootstrap_sor",
        f"roost_sweeps.regime={regime}",
    )

    # -------------------------------------------------
    # Verify materialized run through OWL
    # -------------------------------------------------

    from owlroost.schema.sweeps.regime import (
        MARKET_REGIMES,
    )

    plan = load_run_plan(
        session,
        run_id=0,
    )

    assert plan.rateFrm == MARKET_REGIMES[regime][0]

    assert plan.rateTo == MARKET_REGIMES[regime][1]


def test_materialize_rates_from_to(
    build_session,
    load_run_plan,
    load_trial_toml,
):
    """
    Verify rates_from_to materialization
    survives the entire BUILD pipeline.
    """

    session = build_session(
        "case_alex+jamie.toml",
        "rates_selection.method=bootstrap_sor",
        "roost_sweeps.rates_from_to=1928-2020",
    )

    # -------------------------------------------------
    # Verify materialized run through OWL
    # -------------------------------------------------

    plan = load_run_plan(
        session,
        run_id=0,
    )

    assert plan.rateFrm == 1928
    assert plan.rateTo == 2020


def test_materialize_optimization_goal(
    build_session,
    load_run_plan,
    load_trial_toml,
):
    """
    Verify optimization_goal materialization
    survives the entire BUILD pipeline.
    """

    session = build_session(
        "case_alex+jamie.toml",
        "roost_sweeps.optimization_goal=maxBeq-100",
    )

    # -------------------------------------------------
    # Verify materialized run through OWL
    # -------------------------------------------------

    plan = load_run_plan(
        session,
        run_id=0,
    )

    assert plan.objective == "maxBequest"

    assert plan.solverOptions["netSpending"] == 100
