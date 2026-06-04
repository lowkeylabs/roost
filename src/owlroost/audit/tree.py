# src/owlroost/audit/tree.py

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
# Helpers
# =========================================================


def _has_module_docstring(
    source: str,
) -> bool:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False

    return ast.get_docstring(tree) is not None


def _has_future_import(
    source: str,
) -> bool:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False

    for node in tree.body:
        if not isinstance(
            node,
            ast.ImportFrom,
        ):
            continue

        if node.module != "__future__":
            continue

        for alias in node.names:
            if alias.name == "annotations":
                return True

    return False


def _strip_existing_header(
    lines: list[str],
) -> list[str]:
    if lines and lines[0].strip().startswith("# src/owlroost/"):
        return lines[1:]

    return lines


def _strip_existing_future_import(
    lines: list[str],
) -> list[str]:
    return [line for line in lines if line.strip() != FUTURE_IMPORT]


def _find_docstring_bounds(
    source: str,
) -> tuple[int, int] | None:
    """
    Return 1-based start/end lines
    for module docstring.
    """

    try:
        tree = ast.parse(source)
    except SyntaxError:
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

    return (
        first.lineno,
        first.end_lineno,
    )


def canonicalize_file_structure(
    path: Path,
) -> bool:
    """
    Ensure required module structure exists
    without reformatting the file.

    Ruff owns formatting.
    TREE owns structural requirements.
    """

    source = path.read_text(
        encoding="utf-8",
    )

    original = source

    lines = source.splitlines()

    expected_header = f"# {path.as_posix()}"

    # =====================================================
    # Path Header
    # =====================================================

    if not lines or lines[0].strip() != expected_header:
        if lines and lines[0].strip().startswith("# src/owlroost/"):
            lines[0] = expected_header
        else:
            lines.insert(
                0,
                expected_header,
            )

    source = "\n".join(lines)

    # =====================================================
    # Module Docstring
    # =====================================================

    if not _has_module_docstring(
        source,
    ):
        lines = source.splitlines()

        insert_at = 1

        doc_block = [
            "",
            *CANONICAL_DOCSTRING,
            "",
        ]

        lines[insert_at:insert_at] = doc_block

        source = "\n".join(lines)

    # =====================================================
    # Future Import
    # =====================================================

    if not _has_future_import(
        source,
    ):
        lines = source.splitlines()

        bounds = _find_docstring_bounds(
            source,
        )

        if bounds:
            _start, end = bounds
            insert_at = end
        else:
            insert_at = 1

        lines.insert(insert_at, "")

        lines.insert(
            insert_at + 1,
            FUTURE_IMPORT,
        )

        lines.insert(insert_at + 2, "")

        source = "\n".join(lines)

    # =====================================================
    # Preserve Ruff formatting
    # =====================================================

    new_source = source.rstrip() + "\n"

    if new_source == original:
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

        expected_header = f"# {path.as_posix()}"

        # =================================================
        # Path Header
        # =================================================

        header_ok = bool(lines) and lines[0].strip() == expected_header

        if not header_ok:
            failures += 1

            print()
            print("PATH HEADER ISSUE")
            print(f"  file: {path}")

            if lines and lines[0].strip().startswith("# src/owlroost/"):
                print(f"  found:    {lines[0].strip()}")
            else:
                print("  found:    missing")

            print(f"  expected: {expected_header}")

        # =================================================
        # Docstring
        # =================================================

        if not _has_module_docstring(
            source,
        ):
            failures += 1

            print()
            print("MISSING MODULE DOCSTRING")
            print(f"  file: {path}")

        # =================================================
        # Future Import
        # =================================================

        if not _has_future_import(
            source,
        ):
            failures += 1

            print()
            print("MISSING FUTURE IMPORT")
            print(f"  file: {path}")

        # =================================================
        # Fix
        # =================================================

        if fix:
            changed = canonicalize_file_structure(path)

            if changed:
                fixes += 1

                print()
                print(f"FIXED: {path}")

    print()

    if fix and fixes:
        print(f"UPDATED {fixes} file(s)")
        print()

    return failures
