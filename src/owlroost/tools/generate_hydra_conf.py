# src/owlroost/tools/generate_hydra_conf.py

"""
Generate Hydra conf/**/default.yaml and config.yaml
from the canonical schema registry.

Notes
-----
Uses the SchemaRegistry as the sole source
of truth.

All Hydra-configurable variables originate
from schema registration:

    - OWL bridge fields
    - ROOST section fields
    - sweep fields

Defaults are sourced directly from
FieldSpec.default.

Architectural Invariant
-----------------------
Hydra configuration generation consumes
SchemaRegistry only.

It does not inspect section models,
plugins, or Pydantic classes.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import yaml

from owlroost.schema.bootstrap import (
    build_schema_registry,
)

CONF_ROOT = Path("src/owlroost/conf")

# =========================================================
# Tree Helpers
# =========================================================


def insert_path(
    tree: dict,
    path: tuple[str, ...],
    value: Any,
):
    """
    Insert value into nested dictionary tree.
    """

    cur = tree

    for key in path[:-1]:
        if key not in cur or not isinstance(
            cur[key],
            dict,
        ):
            cur[key] = {}

        cur = cur[key]

    cur[path[-1]] = value


def split_by_root(
    fields,
):
    """
    Group fields by top-level Hydra section.
    """

    groups = {}

    for field in fields:
        if not field.path:
            continue

        root = field.path[0]

        groups.setdefault(
            root,
            [],
        ).append(field)

    return groups


# =========================================================
# Value Normalization
# =========================================================


def normalize_value(
    value,
):
    """
    Normalize values for YAML emission.
    """

    if (
        isinstance(
            value,
            (
                str,
                int,
                float,
                bool,
            ),
        )
        or value is None
    ):
        return value

    if isinstance(
        value,
        (
            list,
            tuple,
        ),
    ):
        return list(value)

    if isinstance(
        value,
        dict,
    ):
        return value

    return str(value)


# =========================================================
# Hydra Field Selection
# =========================================================

HYDRA_SOURCES = {
    "input",
    "discovered",
    "sweep",
}


def hydra_fields(
    reg,
):
    """
    Return fields eligible for Hydra config.
    """

    out = []

    for field in reg.all():
        if not field.path:
            continue

        if field.source not in HYDRA_SOURCES:
            continue

        out.append(field)

    return out


# =========================================================
# Generate Group Configs
# =========================================================


def generate_group_configs(
    reg,
):
    """
    Generate conf/<group>/default.yaml files.
    """

    groups = split_by_root(
        hydra_fields(reg),
    )

    generated_groups = []

    for group_name, fields in groups.items():
        if group_name == "hydra":
            continue

        group_dir = CONF_ROOT / group_name

        group_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        tree = {}

        for field in fields:
            subpath = field.path[1:] if len(field.path) > 1 else field.path

            value = normalize_value(
                field.default,
            )

            insert_path(
                tree,
                subpath,
                value,
            )

        # -------------------------------------------------
        # Minimal OWL validity safeguard
        # -------------------------------------------------

        if group_name == "basic_info":
            tree.setdefault(
                "status",
                "single",
            )
            tree.setdefault(
                "names",
                ["A"],
            )
            tree.setdefault(
                "life_expectancy",
                [90],
            )

        file_path = group_dir / "default.yaml"

        with open(
            file_path,
            "w",
        ) as fh:
            yaml.dump(
                tree,
                fh,
                sort_keys=False,
            )

        print(f"Generated: {file_path}")

        generated_groups.append(group_name)

    return sorted(set(generated_groups))


# =========================================================
# Generate config.yaml
# =========================================================


def generate_config_yaml(
    groups,
):
    defaults = []

    defaults.extend(
        [
            {
                "case": "default",
            },
        ]
    )

    defaults.extend([{group: "default"} for group in groups if group != "case"])

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
        "session": {"id": ("${now:%Y-%m-%d}_${now:%H-%M-%S}")},
        "hydra": {
            "job": {
                "chdir": True,
                "name": "run",
            },
        },
    }

    file_path = CONF_ROOT / "config.yaml"

    with open(
        file_path,
        "w",
    ) as fh:
        yaml.dump(
            config,
            fh,
            sort_keys=False,
        )

    print(f"Generated: {file_path}")


# =========================================================
# Generate Hydra Scaffolding
# =========================================================


def generate_hydra_scaffolding():
    hydra_root = CONF_ROOT / "hydra"

    sweep_basic = hydra_root / "sweep" / "basic.yaml"

    sweep_basic.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        sweep_basic,
        "w",
    ) as fh:
        yaml.dump(
            {"dir": "."},
            fh,
            sort_keys=False,
        )

    sweep_flat = hydra_root / "sweep" / "flat.yaml"

    with open(
        sweep_flat,
        "w",
    ) as fh:
        yaml.dump(
            {
                "dir": ("results/${case.name}/${now:%Y-%m-%d}/${now:%H-%M-%S}"),
                "subdir": "run_${hydra:job.num}",
            },
            fh,
            sort_keys=False,
        )

    hydra_logging = hydra_root / "hydra_logging" / "disabled.yaml"

    hydra_logging.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        hydra_logging,
        "w",
    ) as fh:
        yaml.dump(
            {
                "version": 1,
                "disable_existing_loggers": True,
            },
            fh,
            sort_keys=False,
        )

    job_logging = hydra_root / "job_logging" / "disabled.yaml"

    job_logging.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        job_logging,
        "w",
    ) as fh:
        yaml.dump(
            {
                "version": 1,
                "disable_existing_loggers": True,
            },
            fh,
            sort_keys=False,
        )


# =========================================================
# Main
# =========================================================


def generate():
    if CONF_ROOT.exists():
        shutil.rmtree(
            CONF_ROOT,
        )

    CONF_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    reg = build_schema_registry()

    groups = generate_group_configs(
        reg,
    )

    generate_config_yaml(
        groups,
    )

    generate_hydra_scaffolding()


# =========================================================
# Entry Point
# =========================================================

if __name__ == "__main__":
    generate()
