# src/owlroost/schema/bootstrap.py
#
# Copyright (c) 2026 John Leonard
# All rights reserved.
# SPDX-License-Identifier: LicenseRef-OwlRoost-Proprietary
# See LICENSE file in repository root.

"""
Schema bootstrap.

Notes
-----
Constructs the canonical SchemaRegistry.

Initialization Order
--------------------

1. OWL bridge fields
2. ROOST schema sections
3. Hydra sweep fields

Architectural Invariant
-----------------------

Schema owns executable input ontology.

Catalog consumes schema ontology.

Display consumes catalog ontology.
"""

from __future__ import annotations

from owlroost.schema.owl import (
    register_owl_fields,
)
from owlroost.schema.registry import (
    SchemaRegistry,
)
from owlroost.schema.sections import (
    register_sections,
)
from owlroost.schema.sweeps import (
    register_sweeps,
)

# =========================================================
# Bootstrap
# =========================================================


def build_schema_registry():
    """
    Construct fully initialized
    SchemaRegistry.
    """

    reg = SchemaRegistry()

    # =====================================================
    # OWL Canonical Inputs
    # =====================================================

    register_owl_fields(
        reg,
    )

    # =====================================================
    # ROOST Sections
    # =====================================================

    register_sections(
        reg,
    )

    # =====================================================
    # Sweep Variables
    # =====================================================

    register_sweeps(
        reg,
    )

    return reg
