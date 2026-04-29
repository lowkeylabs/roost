from pathlib import Path

import pytest
import yaml

import owlroost
from owlroost.domain.models.case import EXTRA_SECTION_REGISTRY

# ------------------------------------------------------------
# Locate conf directory robustly
# ------------------------------------------------------------

CONF_ROOT = Path(owlroost.__file__).resolve().parent / "conf"


# ------------------------------------------------------------
# Auto-derive Hydra-backed extension models
# ------------------------------------------------------------


def _hydra_extension_map():
    """
    Derive Hydra extension groups from EXTRA_SECTION_REGISTRY,
    excluding non-configurable sections like 'cache'.
    """
    return {name: model for name, model in EXTRA_SECTION_REGISTRY.items() if name != "cache"}


# ------------------------------------------------------------
# Utility
# ------------------------------------------------------------


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text()) or {}


# ============================================================
# 1️⃣ Hydra keys must exist in Pydantic model
# ============================================================


@pytest.mark.parametrize("group,model", _hydra_extension_map().items())
def test_hydra_keys_subset_of_model_fields(group, model):
    hydra_path = CONF_ROOT / group / "default.yaml"

    # If config group exists, validate it
    if hydra_path.exists():
        hydra_keys = set(_load_yaml(hydra_path).keys())
        model_fields = set(model.model_fields.keys())

        unknown = hydra_keys - model_fields

        assert not unknown, f"[{group}] Hydra keys not defined in {model.__name__}: {unknown}"


# ============================================================
# 2️⃣ Registered extension groups must have conf folder
# ============================================================


def test_registered_extension_groups_have_conf_folder():
    for group in _hydra_extension_map().keys():
        path = CONF_ROOT / group
        assert path.exists(), f"Missing conf group for extension '{group}'"


# ============================================================
# 3️⃣ Hydra defaults must match Pydantic defaults
# (excluding dynamic default_factory fields)
# ============================================================


@pytest.mark.parametrize("group,model", _hydra_extension_map().items())
def test_hydra_defaults_match_model_defaults(group, model):
    hydra_path = CONF_ROOT / group / "default.yaml"

    if not hydra_path.exists():
        pytest.skip(f"No default.yaml for {group}")

    hydra_data = _load_yaml(hydra_path)
    model_instance = model()
    model_defaults = model_instance.model_dump()

    for key, value in hydra_data.items():
        field = model.model_fields.get(key)

        # Skip fields using default_factory (dynamic defaults)
        if field and field.default_factory is not None:
            continue

        model_val = model_defaults.get(key)

        # Normalize sentinel equivalence
        if key in ("essential_spending", "lifestyle_spending"):
            if model_val is None and value == 0:
                continue  # valid equivalence

        assert model_val == value, (
            f"[{group}] Default mismatch for '{key}': " f"Hydra={value} | Model={model_val}"
        )


# ============================================================
# 4️⃣ Hydra config must be instantiable into model
# ============================================================


@pytest.mark.parametrize("group,model", _hydra_extension_map().items())
def test_hydra_config_instantiates_model(group, model):
    hydra_path = CONF_ROOT / group / "default.yaml"

    if not hydra_path.exists():
        pytest.skip(f"No default.yaml for {group}")

    hydra_data = _load_yaml(hydra_path)

    try:
        model(**hydra_data)
    except Exception as e:
        pytest.fail(f"[{group}] Hydra config cannot instantiate {model.__name__}: {e}")
