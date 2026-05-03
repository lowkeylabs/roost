# src/owlroost/display/discovery/cases.py

import tomllib
from pathlib import Path


def discover_cases(root: Path):
    rows = []

    for f in sorted(root.glob("*.toml")):
        try:
            data = tomllib.loads(f.read_text())
        except Exception:
            continue

        rows.append(
            {
                "_path": f,
                "_inputs": data,
                "_metrics": None,
                "_meta": {},
            }
        )

    return rows
