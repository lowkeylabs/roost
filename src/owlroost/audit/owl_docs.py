# src/owlroost/audit/owl_docs.py

"""
OWL documentation audit.

Notes
-----
Validates consistency between the OWL
Pydantic schema and generated OWL
parameter documentation.

Model B2 Architecture
---------------------

OWL Schema
    owns executable OWL inputs

OWL_PARAMETER_DOCS
    owns supplemental documentation

Architectural Invariant
-----------------------

Documentation must describe variables
that actually exist in the OWL schema.

The documentation layer must not become
a second source of truth.

This audit validates:

    - documented variables exist
    - schema variables are documented
    - documentation keys are unique

The audit intentionally does NOT
validate:

    - catalog ontology
    - metrics ontology
    - display ontology

Those responsibilities belong to:

    audit_catalog()
    audit_ontology()
    audit_display()
"""

from __future__ import annotations

from collections import (
    defaultdict,
)

from owlplanner.config.schema import (
    CaseConfig,
    SolverOptions,
)

from owlroost.schema.generated.owl_parameter_docs import (
    OWL_PARAMETER_DOCS,
)
from owlroost.schema.utils import (
    walk_model,
)

# =========================================================
# OWL Expansions
# =========================================================

EXPANSIONS = {
    "solver_options": SolverOptions,
}

# =========================================================
# Audit
# =========================================================


def audit_owl_docs() -> int:
    """
    Audit OWL schema documentation
    consistency.
    """

    print("OWL DOCS")
    print("--------")

    failures = 0

    # =====================================================
    # Discover OWL Schema Variables
    # =====================================================

    schema_variables = {}

    leaf_usage = defaultdict(
        list,
    )

    for name, field in walk_model(
        "",
        CaseConfig,
        expansions=EXPANSIONS,
    ):
        leaf_name = name.split(".")[-1]

        schema_variables[leaf_name] = name

        leaf_usage[leaf_name].append(
            name,
        )

    schema_leaf_names = set(
        schema_variables,
    )

    documented_names = set(
        OWL_PARAMETER_DOCS,
    )

    # =====================================================
    # Documentation Without Schema
    # =====================================================

    print("FOUND IN OWL_DOCS BUT NOT IN SCHEMA")
    print("-----------------------------------")

    orphan_docs = sorted(documented_names - schema_leaf_names)

    if orphan_docs:
        failures += len(
            orphan_docs,
        )

        for name in orphan_docs:
            print(
                name,
            )

    else:
        print("OK")

    # =====================================================
    # Schema Without Documentation
    # =====================================================

    print()
    print("SCHEMA VARIABLES NOT FOUND IN OWL_DOCS")
    print("--------------------------------------")

    undocumented = sorted(schema_leaf_names - documented_names)

    if undocumented:
        failures += len(
            undocumented,
        )

        for name in undocumented:
            print(
                name,
            )

    else:
        print("OK")

    # =====================================================
    # Documentation Key Collisions
    # =====================================================

    print()
    print("DOC KEY COLLISIONS")
    print("------------------")

    collisions = {
        key: paths
        for (
            key,
            paths,
        ) in leaf_usage.items()
        if len(paths) > 1
    }

    if collisions:
        failures += len(
            collisions,
        )

        for (
            key,
            paths,
        ) in sorted(
            collisions.items(),
        ):
            print(f"{key}:")

            for path in paths:
                print(f"    {path}")

    else:
        print("OK")

    # =====================================================
    # Summary
    # =====================================================

    print()
    print("SUMMARY")
    print("-------")

    print(f"OWL schema variables:     {len(schema_leaf_names)}")

    print(f"OWL_DOC entries:     {len(documented_names)}")

    print(f"Found in OWL_DOCS only:              {len(orphan_docs)}")

    print(f"Schema vars missing from OWL_DOCS:   {len(undocumented)}")

    print(f"Collisions:               {len(collisions)}")

    print(f"Total issues:             {failures}")

    print()

    return failures
