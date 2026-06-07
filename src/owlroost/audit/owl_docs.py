# src/owlroost/audit/owl_docs.py
#
# Copyright (c) 2026 John Leonard
# All rights reserved.
# SPDX-License-Identifier: LicenseRef-OwlRoost-Proprietary
# See LICENSE file in repository root.

"""
OWL documentation audit.

Notes
-----
Validates consistency between the OWL
Pydantic schema and generated OWL
parameter documentation.

This audit intentionally distinguishes:

    - architectural failures
    - documentation drift

Documentation drift is reported as a
warning but does not fail the audit.

Architectural failures indicate the
documentation lookup model itself has
become unusable.
"""

from __future__ import annotations

from collections import defaultdict

from owlplanner.config.schema import (
    CaseConfig,
    SolverOptions,
)
from owlplanner.version import __version__ as OWL_VERSION

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
# Alias Normalization
# =========================================================


def build_alias_map() -> dict[str, str]:
    """
    Map OWL Python names to public TOML names.

    Examples
    --------

        maxTime -> max_time
        absTol  -> absTol
    """

    aliases = {}

    for py_name, field in SolverOptions.model_fields.items():
        aliases[py_name] = field.alias if field.alias is not None else py_name

    return aliases


# =========================================================
# Audit
# =========================================================


def audit_owl_docs() -> int:
    """
    Audit OWL schema documentation
    consistency.

    Returns
    -------
    int
        Number of architectural failures.
    """

    print("OWL DOCS")
    print("--------")

    failures = 0
    warnings = 0

    alias_map = build_alias_map()

    # =====================================================
    # Discover OWL Schema Variables
    # =====================================================

    schema_variables = {}

    leaf_usage = defaultdict(
        list,
    )

    for name, _field in walk_model(
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

    documented_names = {
        alias_map.get(
            name,
            name,
        )
        for name in OWL_PARAMETER_DOCS
    }

    orphan_docs = sorted(
        documented_names - schema_leaf_names,
    )

    undocumented = sorted(
        schema_leaf_names - documented_names,
    )

    collisions = {
        key: paths
        for (
            key,
            paths,
        ) in leaf_usage.items()
        if len(paths) > 1
    }

    # =====================================================
    # Warnings
    # =====================================================

    print("WARNINGS")
    print("--------")

    warning_count = 0

    if orphan_docs:
        warning_count += len(
            orphan_docs,
        )

        print()
        print("Documentation entries not found in schema:")

        for name in orphan_docs[:20]:
            print(f"  {name}")

        if len(orphan_docs) > 20:
            print(f"  ... +{len(orphan_docs) - 20} more")

    if undocumented:
        warning_count += len(
            undocumented,
        )

        print()
        print("Schema variables missing documentation:")

        for name in undocumented[:20]:
            print(f"  {name}")

        if len(undocumented) > 20:
            print(f"  ... +{len(undocumented) - 20} more")

    if collisions:
        warning_count += len(
            collisions,
        )

        print()
        print("Documentation key collisions:")

        for (
            key,
            paths,
        ) in sorted(
            collisions.items(),
        ):
            print(f"  {key}")

            for path in paths:
                print(f"      {path}")

    if warning_count == 0:
        print("OK")

    warnings += warning_count

    # =====================================================
    # Errors
    # =====================================================

    print()
    print("ERRORS")
    print("------")

    #
    # No architectural errors currently
    # defined for OWL docs.
    #

    print("OK")

    # =====================================================
    # Summary
    # =====================================================

    print()
    print("SUMMARY")
    print("-------")

    print(f"OWL version:          {OWL_VERSION}")

    print("OWL docs file:        PARAMETERS.md")

    print(f"OWL schema vars:      {len(schema_leaf_names)}")

    print(f"OWL doc entries:      {len(documented_names)}")

    print(f"Warnings:             {warnings}")

    print(f"Errors:               {failures}")

    print()

    return failures
