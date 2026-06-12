# src/owlroost/schema/owl/rate_models.py
#
# Copyright (c) 2026 John Leonard
# SPDX-License-Identifier: GPL-3.0-or-later
# See LICENSE file in repository root.

"""
OWL rate-model ontology loader.

Notes
-----
Registers OWL configuration variables
declared by OWL rate-model metadata.

The OWL ontology is distributed across:

    - CaseConfig
    - SolverOptions
    - rate-model metadata

This loader contributes ontology
variables originating from rate-model
metadata.

Architectural Invariant
-----------------------
One semantic variable produces one
schema identity.

Rate-model metadata may describe
variables already represented in the
Pydantic schema.

Those variables are not duplicated.
"""

from __future__ import annotations

from owlplanner.rate_models.loader import (
    _RATE_MODEL_REGISTRY,
)

from owlroost.catalog.ontology import (
    CatalogNodeType,
)
from owlroost.core.utils import (
    normalize_module_path,
)

from ..registry import (
    FieldSpec,
)

# =========================================================
# Public Ontology Name Mapping
# =========================================================

#
# OWL sometimes uses internal parameter
# names that differ from public TOML
# names.
#
# Example:
#
#     frm -> from
#
# The schema registry always uses
# public ontology names.
#

PUBLIC_NAME_MAP = {
    "frm": "from",
}

# =========================================================
# Helpers
# =========================================================


def _public_name(
    parameter_name: str,
) -> str:
    """
    Convert internal parameter names
    into public ontology names.
    """

    return PUBLIC_NAME_MAP.get(
        parameter_name,
        parameter_name,
    )


def _field_exists(
    reg,
    field_name: str,
) -> bool:
    """
    Best-effort duplicate detection.
    """

    try:
        return (
            reg.get(
                field_name,
            )
            is not None
        )

    except Exception:
        pass

    try:
        return any(field.name == field_name for field in reg.all())

    except Exception:
        pass

    return False


def _register_parameter(
    reg,
    *,
    parameter_name,
    parameter_spec,
    model_class,
):
    """
    Register a single ontology variable.
    """

    public_name = _public_name(
        parameter_name,
    )

    field_name = f"rates_selection.{public_name}"

    # =====================================
    # Preserve canonical semantic identity
    # =====================================

    if _field_exists(
        reg,
        field_name,
    ):
        return

    reg.register(
        FieldSpec(
            # =================================
            # Identity
            # =================================
            name=field_name,
            # =================================
            # Typing
            # =================================
            dtype=parameter_spec.get(
                "type",
                "object",
            ),
            # =================================
            # Runtime Realization
            # =================================
            path=(
                "rates_selection",
                public_name,
            ),
            source="input",
            # =================================
            # Ontology
            # =================================
            owner="OWL",
            semantic_domain="design",
            value_origin="user-specified",
            projection_kind="canonical",
            analytic_kind="primary",
            materialization_level="case",
            node_type=CatalogNodeType.VARIABLE,
            # =================================
            # Documentation
            # =================================
            description=parameter_spec.get(
                "description",
                "",
            ),
            # =================================
            # Provenance
            # =================================
            defined_in=normalize_module_path(
                model_class.__module__,
            ),
        )
    )


# =========================================================
# Registration
# =========================================================


def register_schema_fields(
    reg,
):
    """
    Register ontology variables declared
    by OWL rate-model metadata.
    """

    for (
        _method_name,
        model_class,
    ) in sorted(
        _RATE_MODEL_REGISTRY.items(),
    ):
        metadata = model_class.get_metadata()

        required_parameters = metadata.get(
            "required_parameters",
            {},
        )

        optional_parameters = metadata.get(
            "optional_parameters",
            {},
        )

        for (
            parameter_name,
            parameter_spec,
        ) in required_parameters.items():
            _register_parameter(
                reg,
                parameter_name=parameter_name,
                parameter_spec=parameter_spec,
                model_class=model_class,
            )

        for (
            parameter_name,
            parameter_spec,
        ) in optional_parameters.items():
            _register_parameter(
                reg,
                parameter_name=parameter_name,
                parameter_spec=parameter_spec,
                model_class=model_class,
            )
