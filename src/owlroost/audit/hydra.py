# src/owlroost/audit/hydra.py
#
# Copyright (c) 2026 John Leonard
# All rights reserved.
# SPDX-License-Identifier: LicenseRef-OwlRoost-Proprietary
# See LICENSE file in repository root.

"""
Hydra configuration audit.

Notes
-----
Validates consistency between the
canonical schema registry and generated
Hydra configuration files.

Model B2 Architecture
---------------------

Schema
    owns executable input ontology

Hydra
    is a generated artifact

Architectural Invariant
-----------------------

Hydra configuration generation consumes
SchemaRegistry only.

This audit validates that every
Hydra-eligible schema field is present
in the generated Hydra YAML hierarchy.

The audit intentionally validates:

    schema field
        ->
    generated YAML path

rather than comparing YAML scalar leaves.

Dictionary-valued defaults are treated
as values, not additional schema fields.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from owlroost.schema.bootstrap import (
    build_schema_registry,
)
from owlroost.tools.generate_hydra_conf import (
    hydra_fields,
)

# =========================================================
# Constants
# =========================================================

CONF_ROOT = Path(
    "src/owlroost/conf",
)

# =========================================================
# Helpers
# =========================================================


def path_exists(
    obj,
    path: tuple[str, ...],
) -> bool:
    """
    Verify a schema path exists inside
    generated Hydra YAML.

    Example
    -------

    path:

        (
            "auto_workers_by_solver",
        )

    matches:

        auto_workers_by_solver:
            MOSEK: 8
            HiGHS: 8

    because the field itself exists.

    The contents of the dictionary are
    considered field values rather than
    additional schema fields.
    """

    cur = obj

    for key in path:
        if not isinstance(
            cur,
            dict,
        ):
            return False

        if key not in cur:
            return False

        cur = cur[key]

    return True


def load_group_yaml(
    group_name: str,
):
    """
    Load conf/<group>/default.yaml.
    """

    path = CONF_ROOT / group_name / "default.yaml"

    if not path.exists():
        return None

    return (
        yaml.safe_load(
            path.read_text(),
        )
        or {}
    )


# =========================================================
# Audit
# =========================================================


def audit_hydra() -> int:
    """
    Audit Hydra generation consistency.
    """

    print("HYDRA")
    print("-----")

    failures = 0

    # =====================================================
    # Schema
    # =====================================================

    schema_registry = build_schema_registry()

    eligible_fields = list(
        hydra_fields(
            schema_registry,
        )
    )

    # =====================================================
    # Missing Paths
    # =====================================================

    print("MISSING FROM HYDRA")
    print("------------------")

    missing = []

    for field in eligible_fields:
        group_name = field.path[0]

        yaml_data = load_group_yaml(
            group_name,
        )

        if yaml_data is None:
            missing.append(".".join(field.path))
            continue

        subpath = field.path[1:] if len(field.path) > 1 else field.path

        if not path_exists(
            yaml_data,
            tuple(subpath),
        ):
            missing.append(".".join(field.path))

    if missing:
        failures += len(
            missing,
        )

        for name in sorted(missing)[:25]:
            print(name)

        if len(missing) > 25:
            print(f"... +{len(missing) - 25} more")

    else:
        print("OK")

    # =====================================================
    # Orphan Groups
    # =====================================================

    print()
    print("ORPHAN GROUPS")
    print("-------------")

    expected_groups = {field.path[0] for field in eligible_fields}

    generated_groups = {
        path.name for path in CONF_ROOT.iterdir() if path.is_dir() and path.name != "hydra"
    }

    orphan_groups = sorted(generated_groups - expected_groups)

    if orphan_groups:
        failures += len(
            orphan_groups,
        )

        for group in orphan_groups:
            print(group)

    else:
        print("OK")

    # =====================================================
    # Summary
    # =====================================================

    print()
    print("SUMMARY")
    print("-------")

    print(f"Hydra-eligible schema fields: {len(eligible_fields)}")

    print(f"Generated groups:            {len(generated_groups)}")

    print(f"Missing fields:             {len(missing)}")

    print(f"Orphan groups:              {len(orphan_groups)}")

    print(f"Total issues:               {failures}")

    print()

    return failures
