# src/owlroost/display/loaders.py

import tomllib
from pathlib import Path

import yaml

from .dataset import Dataset
from .discovery.cases import discover_cases


def load_cases(source="."):
    source = Path(source)

    # ----------------------------------------
    # Directory → glob TOML
    # ----------------------------------------
    if source.is_dir():
        rows = discover_cases(source)
        return Dataset(rows, level="case")

    # ----------------------------------------
    # YAML → list of TOML paths
    # ----------------------------------------
    if source.suffix in (".yml", ".yaml"):
        data = yaml.safe_load(source.read_text())
        rows = []

        for p in data:
            path = Path(p)
            try:
                content = tomllib.loads(path.read_text())
            except Exception:
                continue

            rows.append(
                {
                    "_path": path,
                    "_inputs": content,
                    "_metrics": None,
                    "_meta": {},
                }
            )

        return Dataset(rows, level="case")

    raise ValueError(f"Unsupported source: {source}")
