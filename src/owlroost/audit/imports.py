# src/owlroost/audit/imports.py

from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path

ROOT = Path("src/owlroost")


# =========================================================
# Module Discovery
# =========================================================


def discover_modules() -> set[str]:
    """
    Discover all importable owlroost modules.

    Includes:

        foo/bar.py
            -> foo.bar

    and package names:

        foo/bar/__init__.py
            -> foo.bar
    """

    modules: set[str] = set()

    for path in ROOT.rglob("*.py"):

        module = (
            path.relative_to("src")
            .with_suffix("")
            .as_posix()
            .replace("/", ".")
        )

        modules.add(module)

        #
        # Package alias
        #
        if path.name == "__init__.py":

            package = (
                path.parent.relative_to("src")
                .as_posix()
                .replace("/", ".")
            )

            modules.add(package)

    return modules


# =========================================================
# Import Discovery
# =========================================================


def discover_imports(
    path: Path,
) -> list[str]:
    """
    Return all owlroost imports referenced
    by a source file.
    """

    imports: list[str] = []

    try:

        tree = ast.parse(
            path.read_text(
                encoding="utf-8",
            )
        )

    except SyntaxError:

        return imports

    for node in ast.walk(tree):

        # -------------------------------------
        # from x import y
        # -------------------------------------

        if isinstance(
            node,
            ast.ImportFrom,
        ):

            if (
                node.module
                and node.module.startswith(
                    "owlroost"
                )
            ):
                imports.append(
                    node.module
                )

        # -------------------------------------
        # import x
        # -------------------------------------

        elif isinstance(
            node,
            ast.Import,
        ):

            for alias in node.names:

                if alias.name.startswith(
                    "owlroost"
                ):
                    imports.append(
                        alias.name
                    )

    return imports


# =========================================================
# Audit
# =========================================================


def audit_imports() -> int:
    print("IMPORTS")
    print("-------")

    modules = discover_modules()

    missing: dict[
        str,
        list[Path],
    ] = defaultdict(list)

    for path in sorted(
        ROOT.rglob("*.py")
    ):

        for module in discover_imports(
            path,
        ):

            if module not in modules:

                missing[module].append(
                    path
                )

    failures = 0

    for (
        module,
        refs,
    ) in sorted(
        missing.items()
    ):

        failures += len(refs)

        print()
        print(
            "MISSING MODULE"
        )
        print(
            f"  {module}"
        )
        print()

        print(
            "Referenced By"
        )

        for ref in sorted(
            refs
        ):

            print(
                f"  {ref}"
            )

    print()

    return failures
