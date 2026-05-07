# src/owlroost/display/loaders.py

import tomllib
from pathlib import Path

import yaml

from .dataset import Dataset
from .discovery.cases import find_case_files


# =========================================================
# Helpers
# =========================================================
def _load_case_file(path: Path):
    """
    Load a single TOML case file into dataset row format.
    """

    path = Path(path)

    try:
        content = tomllib.loads(path.read_text())
    except Exception:
        return None

    return {
        "_path": path.resolve(),
        "_inputs": content,
        "_metrics": None,
        "_meta": {},
    }


# =========================================================
# Public loaders
# =========================================================
def load_cases(source="."):
    """
    Load case dataset from:

    - directory of TOML case files
    - YAML list of TOML paths
    """

    source = Path(source)

    # -----------------------------------------------------
    # Directory → discover TOML files
    # -----------------------------------------------------
    if source.is_dir():
        rows = []

        for path in find_case_files(source):
            row = _load_case_file(path)

            if row is not None:
                rows.append(row)

        return Dataset(rows, level="case")

    # -----------------------------------------------------
    # YAML → explicit TOML file list
    # -----------------------------------------------------
    if source.suffix in (".yml", ".yaml"):
        data = yaml.safe_load(source.read_text())

        rows = []

        for p in data:
            row = _load_case_file(Path(p))

            if row is not None:
                rows.append(row)

        return Dataset(rows, level="case")

    raise ValueError(f"Unsupported source: {source}")
