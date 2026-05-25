"""
Generate Hydra conf/**/default.yaml and config.yaml from schema registry.

- Uses full schema registry (all sources)
- Emits complete tree (including None values)
- Ensures Hydra override compatibility

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
# Default extraction (Pydantic fallback)
# =========================================================
def get_default(path: tuple[str, ...], model_index):
    root = path[0]

    model = model_index.get(root)

    if model is None:
        model = model_index.get("_owl")

    if model is None:
        return None

    cur = model
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
    cur = tree

    for key in path[:-1]:
        # -------------------------------------
        # If key missing OR not a dict → fix it
        # -------------------------------------
        if key not in cur or not isinstance(cur[key], dict):
            cur[key] = {}

        cur = cur[key]

    # -------------------------------------
    # Assign leaf value
    # -------------------------------------
    cur[path[-1]] = value


def split_by_root(fields):
    groups = {}
    for f in fields:
        if not f.path:
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
# Hydra Field Selection
# =========================================================

HYDRA_SOURCES = {"input", "discovered", "helper"}


def hydra_fields(reg):
    out = []

    for f in reg.all():
        if not f.path:
            continue

        if f.source not in HYDRA_SOURCES:
            continue

        out.append(f)

    return out


# =========================================================
# Generate default.yaml files
# =========================================================
def generate_group_configs(reg, model_index):
    groups = split_by_root(hydra_fields(reg))

    generated_groups = []

    for group_name, fields in groups.items():
        if group_name == "hydra":
            continue

        group_dir = CONF_ROOT / group_name
        group_dir.mkdir(parents=True, exist_ok=True)

        tree = {}

        for f in fields:
            subpath = f.path[1:] if len(f.path) > 1 else f.path

            # -------------------------------------------------
            # Priority: registry default → model → None
            # -------------------------------------------------
            value = f.default

            if value is None:
                value = get_default(f.path, model_index)

            value = normalize_value(value) if value is not None else None

            # -------------------------------------------------
            # ALWAYS insert (critical for Hydra)
            # -------------------------------------------------
            insert_path(tree, subpath, value)

        # ---------------------------------------------------------
        # Minimal OWL validity safety (optional)
        # ---------------------------------------------------------
        if group_name == "basic_info":
            tree.setdefault("status", "single")
            tree.setdefault("names", ["A"])
            tree.setdefault("life_expectancy", [90])

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

    defaults.extend(
        [
            {"case": "default"},
        ]
    )

    defaults.extend([{g: "default"} for g in groups if g != "case"])

    defaults.extend(
        [
            {"hydra/sweep": "basic"},
            {"override hydra/sweep": "flat"},
            {"override hydra/hydra_logging": "disabled"},
            {"override hydra/job_logging": "disabled"},
            "_self_",
        ]
    )

    config = {
        "defaults": defaults,
        "session": {"id": "${now:%Y-%m-%d}_${now:%H-%M-%S}"},
        "hydra": {
            "job": {
                "chdir": True,
                "name": "run",
            },
        },
    }

    file_path = CONF_ROOT / "config.yaml"

    with open(file_path, "w") as fh:
        yaml.dump(config, fh, sort_keys=False)

    print(f"Generated: {file_path}")


# =========================================================
# Generate Hydra scaffolding
# =========================================================
def generate_hydra_scaffolding():
    hydra_root = CONF_ROOT / "hydra"

    # sweep/basic.yaml
    sweep_basic = hydra_root / "sweep" / "basic.yaml"
    sweep_basic.parent.mkdir(parents=True, exist_ok=True)

    with open(sweep_basic, "w") as fh:
        yaml.dump({"dir": "."}, fh, sort_keys=False)

    print(f"Generated: {sweep_basic}")

    # sweep/flat.yaml (corrected)
    sweep_flat = hydra_root / "sweep" / "flat.yaml"

    with open(sweep_flat, "w") as fh:
        yaml.dump(
            {
                "dir": "results/${case.name}/${now:%Y-%m-%d}/${now:%H-%M-%S}",
                "subdir": "run_${hydra:job.num}",
            },
            fh,
            sort_keys=False,
        )

    print(f"Generated: {sweep_flat}")

    # hydra logging disabled
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

    # job logging disabled
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

    generate_hydra_scaffolding()


# =========================================================
# Entry point
# =========================================================
if __name__ == "__main__":
    generate()
