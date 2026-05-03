"""
Generate Hydra conf/**/default.yaml and config.yaml from schema registry.

- Autodiscovers plugin models (root + model)
- Uses Pydantic models for defaults
- No hardcoded schema mapping
- Generates Hydra config structure

Run:
    python -m owlroost.tools.generate_hydra_conf
"""

from pathlib import Path
from typing import Any

import yaml

from owlroost.schema.bootstrap import build_registry
from owlroost.schema.utils import unwrap_annotation

CONF_ROOT = Path("src/owlroost/conf")


# =========================================================
# Plugin model discovery
# =========================================================
def build_model_index(plugins):
    """
    Build mapping:
        root -> Pydantic model

    Special:
        OWL plugin → stored under "_owl"
    """
    model_index = {}

    for p in plugins:
        model = getattr(p, "model", None)
        root = getattr(p, "root", None)

        if model is None:
            continue

        if root is None:
            model_index["_owl"] = model
        else:
            model_index[root] = model

    return model_index


# =========================================================
# Default extraction
# =========================================================
def get_default(path: tuple[str, ...], model_index):
    root = path[0]

    model = model_index.get(root)

    # fallback to OWL model
    if model is None:
        model = model_index.get("_owl")

    if model is None:
        return None

    cur = model

    # skip root if model explicitly mapped
    parts = path[1:] if root in model_index else path

    for i, part in enumerate(parts):
        if not hasattr(cur, "model_fields"):
            return None

        field = cur.model_fields.get(part)
        if field is None:
            return None

        annotation = unwrap_annotation(field.annotation)

        if i == len(parts) - 1:
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
    if value is None:
        return

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
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    if isinstance(v, (list, tuple)):
        return list(v)
    if isinstance(v, dict):
        return v
    return str(v)


# =========================================================
# Generate default.yaml files
# =========================================================
def generate_group_configs(reg, model_index):
    groups = split_by_root(reg.all())

    generated_groups = []

    for group_name, fields in groups.items():
        # ---------------------------------------------------------
        # Skip non-schema hydra group
        # ---------------------------------------------------------
        if group_name == "hydra":
            continue

        group_dir = CONF_ROOT / group_name
        group_dir.mkdir(parents=True, exist_ok=True)

        tree = {}

        # ---------------------------------------------------------
        # Populate tree from schema defaults
        # ---------------------------------------------------------
        for f in fields:
            # allow root-level fields
            subpath = f.path[1:] if len(f.path) > 1 else f.path

            value = f.default

            # -----------------------------------------------------
            # Skip unset values → prevents partial OWL configs
            # -----------------------------------------------------
            if value is None:
                continue

            value = normalize_value(value)
            insert_path(tree, subpath, value)

        # ---------------------------------------------------------
        # Enforce minimal valid OWL structure (Option 1)
        # ---------------------------------------------------------
        if group_name == "basic_info":
            # Only enforce if section is present or being created
            tree.setdefault("status", "single")
            tree.setdefault("names", ["A"])
            tree.setdefault("life_expectancy", [90])

        # ---------------------------------------------------------
        # Write YAML
        # ---------------------------------------------------------
        file_path = group_dir / "default.yaml"

        with open(file_path, "w") as fh:
            yaml.dump(tree, fh, sort_keys=False)

        print(f"Generated: {file_path}")

        generated_groups.append(group_name)

    return sorted(set(generated_groups))


# =========================================================
# Generate config.yaml
# =========================================================
def generate_config_yaml(groups):
    defaults = []

    # Static base
    defaults.extend(
        [
            "logging: default",
            "case: default",
        ]
    )

    # Schema-driven groups
    defaults.extend([{g: "default"} for g in groups])

    # Hydra plumbing
    defaults.extend(
        [
            "hydra/sweep: basic",
            "override hydra/sweep: flat",
            # "#override hydra/hydra_logging: disabled",
            # "override hydra/job_logging: disabled",
            # "override hydra/launcher: joblib",
            "_self_",
        ]
    )

    config = {
        "defaults": defaults,
        "experiment": {"id": "${now:%Y-%m-%d}_${now:%H-%M-%S}"},
        "hydra": {
            "job": {
                "chdir": True,
                "name": "run",
            },
            "launcher": {
                "n_jobs": 1,
            },
        },
    }

    file_path = CONF_ROOT / "config.yaml"

    with open(file_path, "w") as fh:
        yaml.dump(config, fh, sort_keys=False)

    print(f"Generated: {file_path}")


# =========================================================
# Generate Hydra scaffolding (non-schema)
# =========================================================
def generate_hydra_scaffolding():
    """
    Create minimal Hydra config groups required for sweep + logging.
    """

    hydra_root = CONF_ROOT / "hydra"

    # ----------------------------------------
    # sweep/basic.yaml
    # ----------------------------------------
    sweep_basic = hydra_root / "sweep" / "basic.yaml"
    sweep_basic.parent.mkdir(parents=True, exist_ok=True)

    with open(sweep_basic, "w") as fh:
        yaml.dump({"dir": "."}, fh, sort_keys=False)

    print(f"Generated: {sweep_basic}")

    # ----------------------------------------
    # sweep/flat.yaml
    # ----------------------------------------
    sweep_flat = hydra_root / "sweep" / "flat.yaml"

    with open(sweep_flat, "w") as fh:
        yaml.dump({"dir": ".", "subdir": "."}, fh, sort_keys=False)

    print(f"Generated: {sweep_flat}")

    if 0:
        # ----------------------------------------
        # hydra_logging/disabled.yaml
        # ----------------------------------------
        hydra_logging = hydra_root / "hydra_logging" / "disabled.yaml"
        hydra_logging.parent.mkdir(parents=True, exist_ok=True)

        with open(hydra_logging, "w") as fh:
            yaml.dump(
                {
                    "version": 1,
                    "disable_existing_loggers": True,
                },
                fh,
                sort_keys=False,
            )

        print(f"Generated: {hydra_logging}")

        # ----------------------------------------
        # job_logging/disabled.yaml
        # ----------------------------------------
        job_logging = hydra_root / "job_logging" / "disabled.yaml"
        job_logging.parent.mkdir(parents=True, exist_ok=True)

        with open(job_logging, "w") as fh:
            yaml.dump(
                {
                    "version": 1,
                    "disable_existing_loggers": True,
                },
                fh,
                sort_keys=False,
            )

        print(f"Generated: {job_logging}")


# =========================================================
# Main
# =========================================================
def generate():
    reg, plugins = build_registry(return_plugins=True)

    model_index = build_model_index(plugins)

    groups = generate_group_configs(reg, model_index)

    generate_config_yaml(groups)

    # 👇 ADD THIS
    generate_hydra_scaffolding()


# =========================================================
# Entry point
# =========================================================
if __name__ == "__main__":
    generate()
