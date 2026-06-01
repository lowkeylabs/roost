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
    Rewrite file into canonical form.

    Canonical layout:

        # src/owlroost/...

        \"\"\"
        module docstring
        \"\"\"


        ...
    """

    expected_header = f"# {path.as_posix()}"

    source = path.read_text(
        encoding="utf-8",
    )

    original = source

    lines = source.splitlines()

    # =====================================================
    # Remove path header
    # =====================================================

    lines = _strip_existing_header(
        lines,
    )

    # =====================================================
    # Remove future import
    # =====================================================

    lines = _strip_existing_future_import(
        lines,
    )

    source_without_header = "\n".join(lines)

    # =====================================================
    # Preserve docstring if found
    # =====================================================

    doc_lines: list[str]

    bounds = _find_docstring_bounds(
        source_without_header,
    )

    if bounds:
        start, end = bounds

        doc_lines = lines[start - 1 : end]

        body_lines = lines[: start - 1] + lines[end:]

    else:
        doc_lines = CANONICAL_DOCSTRING.copy()

        body_lines = lines

    # =====================================================
    # Trim leading blank lines
    # =====================================================

    while body_lines and not body_lines[0].strip():
        body_lines.pop(0)

    # =====================================================
    # Rebuild file
    # =====================================================

    rebuilt = [
        expected_header,
        "",
        *doc_lines,
        "",
        FUTURE_IMPORT,
        "",
        *body_lines,
    ]

    new_source = "\n".join(rebuilt) + "\n"

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
