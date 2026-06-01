# src/owlroost/audit/packages.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path("src/owlroost")


def audit_packages() -> int:
    print("PACKAGES")
    print("--------")

    failures = 0

    for init_file in ROOT.rglob("__init__.py"):
        package = init_file.parent

        exported = set()

        tree = ast.parse(init_file.read_text(encoding="utf-8"))

        for node in ast.walk(tree):
            if isinstance(
                node,
                ast.ImportFrom,
            ):
                for alias in node.names:
                    exported.add(alias.name)

        if not exported:
            continue

    print()

    return failures
