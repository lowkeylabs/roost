"""
Generate Hydra conf/**/default.yaml files from the schema registry.

- Uses SchemaRegistry (source="input")
- Uses shared Pydantic walker from schema.utils
- Extracts default values from OWL schema (CaseConfig)
- Produces Hydra-compatible config structure

Run:
    python -m owlroost.tools.generate_hydra_conf
"""

from pathlib import Path
from typing import Any

import yaml

from owlroost.schema.bootstrap import build_registry
from owlroost.schema.system_models import RoostConfig, RuntimeConfig, TrialConfig
from owlroost.schema.utils import unwrap_annotation

# Optional import (for defaults)
try:
    from owlplanner.config.schema import CaseConfig
except ImportError:
    CaseConfig = None


CONF_ROOT = Path("src/owlroost/conf")

MODEL_ROOTS = {
    "basic_info": CaseConfig,
    "savings_assets": CaseConfig,
    "fixed_income": CaseConfig,
    "asset_allocation": CaseConfig,
    "rates_selection": CaseConfig,
    "optimization_parameters": CaseConfig,
    "solver_options": CaseConfig,
    # NEW SYSTEM MODELS
    "trial": TrialConfig,
    "runtime": RuntimeConfig,
    "roost": RoostConfig,
}


# =========================================================
# Default extraction
# =========================================================
def get_default(path: tuple[str, ...]):
    root = path[0]
    model = MODEL_ROOTS.get(root)

    if model is None:
        return None

    cur = model

    for i, part in enumerate(path[1:], start=1):
        if not hasattr(cur, "model_fields"):
            return None

        field = cur.model_fields.get(part)
        if field is None:
            return None

        annotation = unwrap_annotation(field.annotation)

        if i == len(path) - 1:
            if field.default is not None:
                return field.default

            if field.default_factory is not None:
                try:
                    return field.default_factory()
                except Exception:
                    return None

            return None

        cur = annotation

    return None


# =========================================================
# Tree helpers
# =========================================================
def insert_path(tree: dict, path: tuple[str, ...], value: Any):
    cur = tree
    for key in path[:-1]:
        cur = cur.setdefault(key, {})
    cur[path[-1]] = value


def split_by_root(fields):
    groups = {}
    for f in fields:
        if f.source != "input":
            continue
        root = f.path[0]
        groups.setdefault(root, []).append(f)
    return groups


# =========================================================
# Value normalization
# =========================================================
def normalize_value(v):
    """
    Ensure values are YAML-safe.
    """
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v

    if isinstance(v, (list, tuple)):
        return list(v)

    if isinstance(v, dict):
        return v

    # fallback (rare)
    return str(v)


# =========================================================
# Main generator
# =========================================================
def generate():
    reg = build_registry()

    groups = split_by_root(reg.all())

    for group_name, fields in groups.items():
        group_dir = CONF_ROOT / group_name
        group_dir.mkdir(parents=True, exist_ok=True)

        tree = {}

        for f in fields:
            # Skip top-level field itself (Hydra group root)
            if len(f.path) == 1:
                continue

            subpath = f.path[1:]  # remove root

            default = get_default(f.path)
            value = normalize_value(default)

            insert_path(tree, subpath, value)

        file_path = group_dir / "default.yaml"

        with open(file_path, "w") as fh:
            yaml.dump(tree, fh, sort_keys=False)

        print(f"Generated: {file_path}")


# =========================================================
# Entry point
# =========================================================
if __name__ == "__main__":
    generate()
