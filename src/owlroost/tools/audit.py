# src/owlroost/tools/audit.py

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from importlib import import_module

import click

# =========================================================
# Audit Registry
# =========================================================

AUDITS: dict[
    str,
    tuple[str, str],
] = {
    "tree": (
        "owlroost.audit.tree",
        "audit_tree",
    ),
    "imports": (
        "owlroost.audit.imports",
        "audit_imports",
    ),
    "packages": (
        "owlroost.audit.packages",
        "audit_packages",
    ),
    "ontology": (
        "owlroost.audit.ontology",
        "audit_ontology",
    ),
    "catalog": (
        "owlroost.audit.catalog",
        "audit_catalog",
    ),
    "display": (
        "owlroost.audit.display",
        "audit_display",
    ),
    "hydra": (
        "owlroost.audit.hydra",
        "audit_hydra",
    ),
    "owl_docs": (
        "owlroost.audit.owl_docs",
        "audit_owl_docs",
    ),
}


# =========================================================
# Helpers
# =========================================================


def run_audit(
    name: str,
    *,
    fix: bool = False,
) -> int:
    """
    Execute a single audit.

    Returns
    -------
    int
        Number of failures reported.
    """

    module_name, function_name = AUDITS[name]

    try:
        module = import_module(
            module_name,
        )

        audit_fn = getattr(
            module,
            function_name,
        )

        try:
            return audit_fn(
                fix=fix,
            )

        except TypeError:
            #
            # Backwards compatibility
            # for audits that do not yet
            # accept a fix parameter.
            #
            return audit_fn()

    except Exception as err:
        click.echo()

        click.echo(f"{name.upper()} FAILED")

        click.echo(f"    {type(err).__name__}: {err}")

        click.echo()

        return 1


def run_all_audits(
    *,
    fix: bool = False,
) -> int:
    failures = 0

    for name in AUDITS:
        failures += run_audit(
            name,
            fix=fix,
        )

    click.echo()

    if failures:
        click.echo(f"FAILED ({failures} issue(s))")
    else:
        click.echo("PASS")

    return failures


# =========================================================
# CLI
# =========================================================


@click.group(
    invoke_without_command=True,
)
@click.pass_context
def cli(
    ctx: click.Context,
) -> None:
    """
    ROOST architecture audits.
    """

    if ctx.invoked_subcommand is None:
        ctx.invoke(all)


# =========================================================
# All Audits
# =========================================================


@cli.command(
    name="all",
)
@click.option(
    "--fix",
    is_flag=True,
    help=("Apply safe automatic fixes where supported."),
)
def all(
    fix: bool,
) -> None:
    failures = run_all_audits(
        fix=fix,
    )

    raise SystemExit(1 if failures else 0)


# =========================================================
# Tree Audit
# =========================================================


@cli.command(
    name="tree",
)
@click.option(
    "--fix",
    is_flag=True,
    help=(
        "Canonicalize file structure. "
        "Repairs path headers, adds module "
        "docstrings, and inserts "
        "'from __future__ import annotations' "
        "where missing."
    ),
)
def tree_command(
    fix: bool,
) -> None:
    """
    Audit source tree structure.

    Validates canonical file layout:

        # src/owlroost/...

        \"\"\"
        module docstring
        \"\"\"

    """

    failures = run_audit(
        "tree",
        fix=fix,
    )

    raise SystemExit(1 if failures else 0)


# =========================================================
# Imports Audit
# =========================================================


@cli.command()
def imports() -> None:
    failures = run_audit(
        "imports",
    )

    raise SystemExit(1 if failures else 0)


# =========================================================
# Packages Audit
# =========================================================


@cli.command()
def packages() -> None:
    failures = run_audit(
        "packages",
    )

    raise SystemExit(1 if failures else 0)


# =========================================================
# Ontology Audit
# =========================================================


@cli.command()
def ontology() -> None:
    failures = run_audit(
        "ontology",
    )

    raise SystemExit(1 if failures else 0)


# =========================================================
# Ontology Audit
# =========================================================


@cli.command()
def owl_docs() -> None:
    failures = run_audit(
        "owl_docs",
    )

    raise SystemExit(1 if failures else 0)


# =========================================================
# hydra drift
# =========================================================


@cli.command()
def hydra() -> None:
    failures = run_audit(
        "hydra",
    )

    raise SystemExit(1 if failures else 0)


# =========================================================
# Catalog Audit
# =========================================================


@cli.command()
def catalog() -> None:
    failures = run_audit(
        "catalog",
    )

    raise SystemExit(1 if failures else 0)


# =========================================================
# Display Audit
# =========================================================


@cli.command()
def display() -> None:
    failures = run_audit(
        "display",
    )

    raise SystemExit(1 if failures else 0)


# =========================================================
# Entry Point
# =========================================================


def main() -> int:
    cli()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
