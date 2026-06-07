# src/owlroost/audit/tree.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

import ast
from datetime import datetime
from pathlib import Path

ROOT = Path("src/owlroost")

HEADER_OWNER = "John Leonard"

HEADER_YEAR = str(datetime.now().year)

HEADER_TEMPLATE = [
    "# {path}",
    "#",
    "# Copyright (c) {year} {owner}",
    "# SPDX-License-Identifier: GPL-3.0-or-later",
    "# See LICENSE file in repository root.",
]

HEADER_LINES = len(HEADER_TEMPLATE)

CANONICAL_DOCSTRING = [
    '"""',
    "TODO: Document module.",
    "",
    "Notes",
    "-----",
    "Describe responsibilities, ownership,",
    "and architectural role.",
    '"""',
]

FUTURE_IMPORT = "from __future__ import annotations"


# =========================================================
# AST Helpers
# =========================================================


def _parse(
    source: str,
) -> ast.Module | None:
    try:
        return ast.parse(source)

    except SyntaxError:
        return None


def _has_module_docstring(
    tree: ast.Module | None,
) -> bool:
    if tree is None:
        return False

    return ast.get_docstring(tree) is not None


def _has_future_import(
    tree: ast.Module | None,
) -> bool:
    if tree is None:
        return False

    for node in tree.body:
        if not isinstance(
            node,
            ast.ImportFrom,
        ):
            continue

        if node.module != "__future__":
            continue

        if any(alias.name == "annotations" for alias in node.names):
            return True

    return False


def _find_docstring_bounds(
    tree: ast.Module | None,
) -> tuple[int, int] | None:
    """
    Return 1-based start/end lines
    for module docstring.
    """

    if tree is None:
        return None

    if not tree.body:
        return None

    first = tree.body[0]

    if not isinstance(
        first,
        ast.Expr,
    ):
        return None

    if not isinstance(
        first.value,
        ast.Constant,
    ):
        return None

    if not isinstance(
        first.value.value,
        str,
    ):
        return None

    if first.end_lineno is None:
        return None

    return (
        first.lineno,
        first.end_lineno,
    )


# =========================================================
# Header Helpers
# =========================================================


def _build_header(
    path: Path,
) -> list[str]:
    return [
        line.format(
            path=path.as_posix(),
            year=HEADER_YEAR,
            owner=HEADER_OWNER,
        )
        for line in HEADER_TEMPLATE
    ]


def _is_legacy_header(
    lines: list[str],
) -> bool:
    return bool(lines) and lines[0].strip().startswith("# src/owlroost/")


def _has_canonical_header(
    lines: list[str],
    path: Path,
) -> bool:
    return len(lines) >= HEADER_LINES and lines[:HEADER_LINES] == _build_header(path)


def _existing_header_length(
    lines: list[str],
) -> int:
    if not _is_legacy_header(lines):
        return 0

    idx = 1

    while idx < len(lines):
        line = lines[idx]

        if line.startswith("#") or not line.strip():
            idx += 1
            continue

        break

    return idx


# =========================================================
# Canonicalization
# =========================================================


def canonicalize_file_structure(
    path: Path,
) -> bool:
    """
    Ensure required module structure exists.

    Ruff owns formatting.
    TREE owns structural requirements.
    """

    source = path.read_text(
        encoding="utf-8",
    )

    original = source

    lines = source.splitlines()

    # =====================================================
    # Canonical Header
    # =====================================================

    header = _build_header(
        path,
    )

    existing_header_len = _existing_header_length(
        lines,
    )

    body = lines[existing_header_len:]

    # -----------------------------------------------------
    # Install canonical header
    # -----------------------------------------------------

    while body and body[0] == "":
        body.pop(0)

    lines = [
        *header,
        "",
        *body,
    ]

    source = "\n".join(
        lines,
    )

    tree = _parse(source)

    # =====================================================
    # Module Docstring
    # =====================================================

    if not _has_module_docstring(
        tree,
    ):
        lines = source.splitlines()

        lines[HEADER_LINES + 1 : HEADER_LINES + 1] = [
            "",
            *CANONICAL_DOCSTRING,
            "",
        ]

        source = "\n".join(lines)

        tree = _parse(source)

    # =====================================================
    # Future Import
    # =====================================================

    if not _has_future_import(
        tree,
    ):
        lines = source.splitlines()

        bounds = _find_docstring_bounds(tree)

        if bounds:
            insert_at = bounds[1]
            # AST lines are 1-based and list.insert()
            # places after the docstring end.
        else:
            insert_at = HEADER_LINES

        lines.insert(
            insert_at,
            "",
        )

        lines.insert(
            insert_at + 1,
            FUTURE_IMPORT,
        )

        lines.insert(
            insert_at + 2,
            "",
        )

        source = "\n".join(lines)

    new_source = source.rstrip() + "\n"

    changed = new_source != original

    if not changed:
        return False

    path.write_text(
        new_source,
        encoding="utf-8",
    )

    return True


# =========================================================
# Audit
# =========================================================


def audit_tree(
    *,
    fix: bool = False,
) -> int:
    print("TREE")
    print("----")

    failures = 0
    fixes = 0

    for path in sorted(ROOT.rglob("*.py")):
        source = path.read_text(
            encoding="utf-8",
        )

        lines = source.splitlines()

        tree = _parse(source)

        # =================================================
        # Path Header
        # =================================================

        expected = _build_header(path)

        if not _has_canonical_header(lines, path):
            failures += 1

            print()
            print("CANONICAL HEADER ISSUE")
            print(f"  file: {path}")

            if _is_legacy_header(lines):
                print(f"  found:    {lines[0].strip()}")
            else:
                print("  found:    missing")

            print("  expected:")
            for line in expected:
                print(f"    {line}")

        # =================================================
        # Module Docstring
        # =================================================

        if not _has_module_docstring(
            tree,
        ):
            failures += 1

            print()
            print("MISSING MODULE DOCSTRING")
            print(f"  file: {path}")

        # =================================================
        # Future Import
        # =================================================

        if not _has_future_import(
            tree,
        ):
            failures += 1

            print()
            print("MISSING FUTURE IMPORT")
            print(f"  file: {path}")

        # =================================================
        # Fix
        # =================================================

        if fix:
            changed = canonicalize_file_structure(
                path,
            )

            if changed:
                fixes += 1

                print()
                print(f"FIXED: {path}")

    print()

    if fix and fixes:
        print(f"UPDATED {fixes} file(s)")
        print()

    return failures
