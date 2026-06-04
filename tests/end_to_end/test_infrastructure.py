from __future__ import annotations


def test_infrastructure(
    build_session,
    load_run_plan,
    load_trial_toml,
):
    """
    Verify ss_age_pair sweep expansion
    survives the entire BUILD pipeline.
    """

    session = build_session(
        "case_alex+jamie.toml",
        "roost_settings.trials_per_run=10",
        "rates_selection.method=historical_bootstrap",
    )

    # -------------------------------------------------
    # Session structure
    # -------------------------------------------------

    assert (session / "session.toml").exists()

    run0 = session / "run_0"

    assert run0.exists()

    assert (run0 / "run.toml").exists()

    # -------------------------------------------------
    # HFP copied
    # -------------------------------------------------

    assert (run0 / "HFP_alex+jamie.xlsx").exists()

    # -------------------------------------------------
    # Trial hierarchy
    # -------------------------------------------------

    trial_root = run0 / "trials"

    assert trial_root.exists()

    trials = sorted(p for p in trial_root.iterdir() if p.is_dir())

    assert len(trials) == 10

    trial0 = trial_root / "0000"

    assert (trial0 / "trial.toml").exists()

    # -------------------------------------------------
    # Verify materialized run through OWL
    # -------------------------------------------------

    plan = load_run_plan(
        session,
        run_id=0,
    )

    assert plan.rateMethod == "historical_bootstrap"

    # -------------------------------------------------
    # Trial references parent HFP
    # -------------------------------------------------

    trial_dict = load_trial_toml(
        session,
        run_id=0,
        trial_id=0,
    )

    assert "household_financial_profile" in trial_dict

    hfp_name = trial_dict["household_financial_profile"]["HFP_file_name"]

    assert "HFP_alex+jamie.xlsx" in hfp_name
