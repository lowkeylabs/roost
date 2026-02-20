from hydra import compose, initialize_config_module


def test_historical_defaults_present():
    """
    When rates_selection.method=historical,
    roll_sequence and reverse_sequence must exist
    and default to 0 and False respectively.
    """
    with initialize_config_module(
        config_module="owlroost.conf",
        version_base=None,
    ):
        cfg = compose(
            config_name="config",
            overrides=["rates_selection.method=historical"],
        )

    assert cfg.rates_selection.method == "historical"

    assert hasattr(cfg.rates_selection, "roll_sequence")
    assert hasattr(cfg.rates_selection, "reverse_sequence")

    assert cfg.rates_selection.roll_sequence == 0
    assert cfg.rates_selection.reverse_sequence is False


def test_historical_roll_override():
    """
    roll_sequence override should compose cleanly
    and reflect new value.
    """
    with initialize_config_module(
        config_module="owlroost.conf",
        version_base=None,
    ):
        cfg = compose(
            config_name="config",
            overrides=[
                "rates_selection.method=historical",
                "rates_selection.roll_sequence=5",
            ],
        )

    assert cfg.rates_selection.method == "historical"
    assert cfg.rates_selection.roll_sequence == 5
    assert cfg.rates_selection.reverse_sequence is False


def test_historical_reverse_override():
    """
    reverse_sequence override should compose cleanly
    and reflect new value.
    """
    with initialize_config_module(
        config_module="owlroost.conf",
        version_base=None,
    ):
        cfg = compose(
            config_name="config",
            overrides=[
                "rates_selection.method=historical",
                "rates_selection.reverse_sequence=true",
            ],
        )

    assert cfg.rates_selection.method == "historical"
    assert cfg.rates_selection.roll_sequence == 0
    assert cfg.rates_selection.reverse_sequence is True


def test_non_historical_still_has_fields():
    """
    reverse_sequence and roll_sequence should still be present
    even when method is not historical, but they may be ignored
    by the engine.
    """
    with initialize_config_module(
        config_module="owlroost.conf",
        version_base=None,
    ):
        cfg = compose(
            config_name="config",
            overrides=["rates_selection.method=stochastic"],
        )

    assert hasattr(cfg.rates_selection, "roll_sequence")
    assert hasattr(cfg.rates_selection, "reverse_sequence")
