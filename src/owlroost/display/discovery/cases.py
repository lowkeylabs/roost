# src/owlroost/display/discovery/cases.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from pathlib import Path


# =========================================================
# Helpers
# =========================================================
def is_case_file(path: Path):
    """
    Return True if path is a user-authored
    case TOML file.

    Excludes generated artifacts.
    """

    path = Path(path)

    if not path.is_file():
        return False

    if path.suffix != ".toml":
        return False

    excluded = {
        "run.toml",
        "trial.toml",
        "session.toml",
    }

    if path.name in excluded:
        return False

    return True


# =========================================================
# Discovery
# =========================================================
def find_case_files(root="."):
    """
    Find candidate case TOML files.

    Excludes generated artifacts.
    """

    root = Path(root)

    if not root.exists():
        return []

    out = []

    for p in root.iterdir():
        if is_case_file(p):
            out.append(p.resolve())

    return sorted(out)
