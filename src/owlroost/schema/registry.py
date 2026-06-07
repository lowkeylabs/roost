# src/owlroost/schema/registry.py
#
# Copyright (c) 2026 John Leonard
# All rights reserved.
# SPDX-License-Identifier: LicenseRef-OwlRoost-Proprietary
# See LICENSE file in repository root.

"""
TODO: Document module.

Notes
-----
Describe responsibilities, ownership,
and architectural role.
"""

from __future__ import annotations

from owlroost.schema.specs import (
    FieldSpec,
)

# =========================================================
# Schema Registry
# =========================================================


class SchemaRegistry:
    """
    Runtime registry and lookup container
    for executable schema ontology.

    Notes
    -----
    SchemaRegistry intentionally owns only:

        - field registration
        - lookup/indexing
        - iteration

    It intentionally does NOT own:

        - ontology definitions
        - runtime discovery
        - aggregation synthesis
        - catalog indexing
        - display composition
        - reporting behavior

    Canonical semantic ownership belongs
    to FieldSpec and OntologySpec.
    """

    def __init__(
        self,
    ):
        self._fields: dict[
            str,
            FieldSpec,
        ] = {}

    # =====================================================
    # Registration
    # =====================================================

    def register(
        self,
        field: FieldSpec,
    ):
        """
        Register canonical executable schema field.
        """

        if field.name in self._fields:
            raise ValueError(f"Duplicate schema field registered: {field.name}")

        self._fields[field.name] = field

    # =====================================================
    # Lookup
    # =====================================================

    def get(
        self,
        name: str,
    ) -> FieldSpec:
        """
        Retrieve schema field by canonical name.
        """

        try:
            return self._fields[name]

        except KeyError as err:
            raise KeyError(f"Schema field not found: {name}") from err

    def exists(
        self,
        name: str,
    ) -> bool:
        """
        Return whether field exists.
        """

        return name in self._fields

    # =====================================================
    # Iteration
    # =====================================================

    def all(
        self,
    ):
        """
        Iterate over all registered fields.
        """

        return self._fields.values()

    def names(
        self,
    ):
        """
        Iterate over canonical field names.
        """

        return self._fields.keys()

    def items(
        self,
    ):
        """
        Iterate over registry items.
        """

        return self._fields.items()

    # =====================================================
    # Introspection
    # =====================================================

    def __contains__(
        self,
        name: str,
    ):
        return name in self._fields

    def __len__(
        self,
    ):
        return len(self._fields)

    def __iter__(
        self,
    ):
        return iter(self._fields.values())
