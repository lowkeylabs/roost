# src/owlroost/audit/hydra.py

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

Hydra configuration is generated from
the subset of schema fields eligible
for Hydra configuration.

Hydra generation currently includes:

    - input
    - discovered
    - sweep

schema fields.

Hydra generation intentionally excludes:

    - derived fields
    - internal fields
    - runtime materializations
    - metrics
    - display entities
    - catalog entities

This audit therefore validates:

    hydra_fields(schema_registry)

against:

    conf/**/*.yaml

rather than comparing Hydra against
the entire schema registry.

Typical Fix
-----------

Regenerate Hydra configuration:

    python -m owlroost.tools.generate_hydra_conf
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


def schema_to_hydra_name(
    field,
):
    """
    Convert schema field identity into the
    corresponding Hydra field identity.

    Examples
    --------

    case_name
        -> case_name.case_name

    description
        -> description.description

    spending_policy.essential_spending
        -> spending_policy.essential_spending
    """

    if len(field.path) == 1:
        return f"{field.path[0]}.{field.path[0]}"

    return ".".join(field.path)


def _flatten(
    obj,
    prefix=(),
):
    """
    Flatten nested YAML into dotted
    field names.
    """

    result = set()

    if isinstance(
        obj,
        dict,
    ):
        for key, value in obj.items():
            result |= _flatten(
                value,
                prefix + (key,),
            )

    elif isinstance(
        obj,
        list,
    ):
        if prefix:
            result.add(".".join(prefix))

    else:
        if prefix:
            result.add(".".join(prefix))

    return result


def load_hydra_fields():
    """
    Load generated Hydra field names.
    """

    fields = set()

    if not CONF_ROOT.exists():
        return fields

    for group_dir in CONF_ROOT.iterdir():
        if not group_dir.is_dir():
            continue

        default_file = group_dir / "default.yaml"

        if not default_file.exists():
            continue

        try:
            data = yaml.safe_load(default_file.read_text())

        except Exception:
            continue

        data = data or {}

        for path in _flatten(
            data,
        ):
            if path.startswith(group_dir.name + "."):
                fields.add(
                    path,
                )

            else:
                fields.add(f"{group_dir.name}.{path}")

    return fields


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

    eligible_schema_fields = {
        schema_to_hydra_name(
            field,
        )
        for field in hydra_fields(
            schema_registry,
        )
    }

    # =====================================================
    # Hydra
    # =====================================================

    generated_hydra_fields = load_hydra_fields()

    # =====================================================
    # Drift Analysis
    # =====================================================

    missing_from_hydra = eligible_schema_fields - generated_hydra_fields

    stale_hydra_fields = generated_hydra_fields - eligible_schema_fields

    # =====================================================
    # Missing Fields
    # =====================================================

    print("MISSING FROM HYDRA")
    print("------------------")

    if missing_from_hydra:
        failures += len(missing_from_hydra)

        for field_name in sorted(missing_from_hydra)[:25]:
            print(
                field_name,
            )

        if len(missing_from_hydra) > 25:
            print(f"... +{len(missing_from_hydra) - 25} more")

    else:
        print("OK")

    # =====================================================
    # Stale Fields
    # =====================================================

    print()
    print("STALE HYDRA FIELDS")
    print("------------------")

    if stale_hydra_fields:
        failures += len(stale_hydra_fields)

        for field_name in sorted(stale_hydra_fields)[:25]:
            print(
                field_name,
            )

        if len(stale_hydra_fields) > 25:
            print(f"... +{len(stale_hydra_fields) - 25} more")

    else:
        print("OK")

    # =====================================================
    # Summary
    # =====================================================

    print()
    print("SUMMARY")
    print("-------")

    print(f"Hydra-eligible schema fields: {len(eligible_schema_fields)}")

    print(f"Generated Hydra fields:       {len(generated_hydra_fields)}")

    print(f"Missing fields:               {len(missing_from_hydra)}")

    print(f"Stale fields:                 {len(stale_hydra_fields)}")

    print(f"Total issues:                 {failures}")

    print()

    if failures:
        print("Hydra configuration appears stale.")

        print()

        print("Regenerate Hydra configuration from schema.")

        print()

    return failures
