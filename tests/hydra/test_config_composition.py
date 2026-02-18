from hydra import initialize_config_module, compose
from omegaconf import OmegaConf


def test_config_composes_cleanly():
    with initialize_config_module(
        config_module="owlroost.conf",
        version_base=None,
    ):
        cfg = compose(config_name="config")
    assert cfg is not None


def test_required_groups_present():
    with initialize_config_module(
        config_module="owlroost.conf",
        version_base=None,
    ):
        cfg = compose(config_name="config")

    required = [
        "basic_info",
        "savings_assets",
        "fixed_income",
        "asset_allocations",
        "life_expectancy",
        "rates",
        "optimization",
        "solver",
        "trial",
        "roost",
    ]

    for group in required:
        assert hasattr(cfg, group), f"Missing group: {group}"

def test_default_trial_settings():
    with initialize_config_module(
        config_module="owlroost.conf",
        version_base=None,
    ):
        cfg = compose(config_name="config")

    assert cfg.trial.id == 0
    assert cfg.trial.count == 1
    assert cfg.trial.n_jobs == 5

def test_override_trial_count():
    with initialize_config_module(
        config_module="owlroost.conf",
        version_base=None,
    ):
        cfg = compose(
            config_name="config",
            overrides=["trial.count=10"],
        )

    assert cfg.trial.count == 10

def test_override_rates_method():
    with initialize_config_module(
        config_module="owlroost.conf",
        version_base=None,
    ):
        cfg = compose(
            config_name="config",
            overrides=["rates.method=stochastic"],
        )

    assert cfg.rates.method == "stochastic"


def test_launcher_override_resolves():
    with initialize_config_module(
        config_module="owlroost.conf",
        version_base=None,
    ):
        cfg = compose(config_name="config")

    # If launcher group were broken, compose would fail.
    assert cfg.trial.n_jobs == 5
