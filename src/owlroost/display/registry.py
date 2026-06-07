# src/owlroost/display/registry.py
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

from owlroost.display.specs import (
    DisplayDashboard,
    DisplayField,
    DisplayGroup,
    DisplayView,
)


class DisplayRegistry:
    """
    Central registry for display-layer objects.

    Owns:

        - DisplayField
        - DisplayGroup
        - DisplayView

    DisplayRegistry owns presentation
    semantics layered atop canonical
    schema and metrics ontology.

    SchemaRegistry owns meaning.

    DisplayRegistry owns presentation.
    """

    # =====================================================
    # Construction
    # =====================================================

    def __init__(self):
        self._display_fields: dict[
            str,
            DisplayField,
        ] = {}

        self._groups: dict[
            str,
            DisplayGroup,
        ] = {}

        self._views: dict[
            tuple[str, str],
            DisplayView,
        ] = {}

        self._dashboards: dict[
            str,
            DisplayDashboard,
        ] = {}

    # =====================================================
    # Display Fields
    # =====================================================

    def register_display_field(
        self,
        field: DisplayField,
    ):
        """
        Register DisplayField.

        Existing fields are intentionally
        overwritten to support display
        customization and field refinement.
        """

        self._display_fields[field.field_name] = field

    def get_display_field(
        self,
        field_name: str,
    ) -> DisplayField:
        """
        Lookup DisplayField.
        """

        try:
            return self._display_fields[field_name]

        except KeyError as err:
            raise KeyError(f"DisplayField not found: {field_name}") from err

    def has_display_field(
        self,
        field_name: str,
    ) -> bool:
        """
        Return True if field exists.
        """

        return field_name in self._display_fields

    def all_display_fields(
        self,
    ) -> list[DisplayField]:
        """
        Return all DisplayFields.
        """

        return list(self._display_fields.values())

    # -----------------------------------------------------
    # Compatibility Aliases
    # -----------------------------------------------------

    def all(
        self,
    ) -> list[DisplayField]:
        """
        Compatibility alias.

        Returns all display fields.
        """

        return self.all_display_fields()

    def get_all_display_fields(
        self,
    ) -> list[DisplayField]:
        return self.all_display_fields()

    # =====================================================
    # Groups
    # =====================================================

    def register_group(
        self,
        group: DisplayGroup,
    ):
        key = group.key

        if key in self._groups:
            raise ValueError(f"Duplicate DisplayGroup registered: {key}")

        self._groups[key] = group

    def get_group(
        self,
        key: str,
    ) -> DisplayGroup:
        try:
            return self._groups[key]

        except KeyError as err:
            raise KeyError(f"DisplayGroup not found: {key}") from err

    def has_group(
        self,
        key: str,
    ) -> bool:
        return key in self._groups

    def all_groups(
        self,
    ) -> list[DisplayGroup]:
        return list(self._groups.values())

    def get_all_groups(
        self,
    ) -> list[DisplayGroup]:
        return self.all_groups()

    # =====================================================
    # Group Expansion
    # =====================================================

    def expand_group(
        self,
        key: str,
    ) -> list[str]:
        """
        Expand a DisplayGroup into a flat
        ordered list of field names.

        Notes
        -----
        Expansion is recursive.

        Duplicate fields are removed while
        preserving first-seen ordering.

        Cyclic group references are rejected.
        """

        expanded: list[str] = []

        visited: set[str] = set()

        def _expand(
            group_key: str,
        ):
            if group_key in visited:
                raise ValueError(f"DisplayGroup cycle detected: {group_key}")

            visited.add(group_key)

            group = self.get_group(group_key)

            for entry in group.entries:
                # -----------------------------------------
                # Implicit field
                # -----------------------------------------

                if isinstance(
                    entry,
                    str,
                ):
                    if not self.has_display_field(entry):
                        raise ValueError(f"Unknown DisplayField: {entry}")

                    expanded.append(entry)

                    continue

                # -----------------------------------------
                # Explicit entry
                # -----------------------------------------

                if not isinstance(
                    entry,
                    tuple,
                ):
                    continue

                if len(entry) != 2:
                    raise ValueError(f"Invalid group entry: {entry}")

                kind, value = entry

                if kind == "field":
                    if not self.has_display_field(value):
                        raise ValueError(f"Unknown DisplayField: {value}")

                    expanded.append(value)

                elif kind == "group":
                    if not self.has_group(value):
                        raise ValueError(f"Unknown DisplayGroup: {value}")

                    _expand(value)

            visited.remove(group_key)

        _expand(key)

        seen: set[str] = set()

        unique: list[str] = []

        for field_name in expanded:
            if field_name in seen:
                continue

            seen.add(field_name)

            unique.append(field_name)

        return unique

    # =====================================================
    # Registry Names
    # =====================================================

    def all_field_names(
        self,
    ) -> list[str]:
        """
        Return all registered field names.
        """

        return sorted(self._display_fields.keys())

    def all_group_names(
        self,
    ) -> list[str]:
        """
        Return all registered group names.
        """

        return sorted(self._groups.keys())

    def all_view_keys(
        self,
    ) -> list[tuple[str, str]]:
        """
        Return all registered view keys.

        Returns
        -------
        [
            (level, name),
            ...
        ]
        """

        return sorted(self._views.keys())

    # =====================================================
    # Views
    # =====================================================

    def register_view(
        self,
        view: DisplayView,
    ):
        key = (
            view.level,
            view.name,
        )

        if key in self._views:
            raise ValueError(f"Duplicate DisplayView registered: {view.level}/{view.name}")

        self._views[key] = view

    def get_view(
        self,
        level: str,
        name: str,
    ) -> DisplayView:
        key = (
            level,
            name,
        )

        try:
            return self._views[key]

        except KeyError as err:
            raise KeyError(f"DisplayView not found: {level}/{name}") from err

    def has_view(
        self,
        level: str,
        name: str,
    ) -> bool:
        return (
            level,
            name,
        ) in self._views

    def all_views(
        self,
    ) -> list[DisplayView]:
        return list(self._views.values())

    def get_all_views(
        self,
    ) -> list[DisplayView]:
        return self.all_views()

    # =====================================================
    # View Expansion
    # =====================================================

    def expand_view_fields(
        self,
        level: str,
        name: str,
    ) -> list[str]:
        """
        Expand fields referenced by a view.
        """

        view = self.get_view(
            level,
            name,
        )

        expanded: list[str] = []

        def expand_entries(
            entries,
        ):
            for entry in entries:
                if isinstance(
                    entry,
                    str,
                ):
                    if not self.has_display_field(entry):
                        raise ValueError(f"Unknown DisplayField: {entry}")

                    expanded.append(entry)

                elif isinstance(
                    entry,
                    tuple,
                ):
                    if len(entry) != 2:
                        continue

                    kind, value = entry

                    if kind == "field":
                        if not self.has_display_field(value):
                            raise ValueError(f"Unknown DisplayField: {value}")

                        expanded.append(value)

                    elif kind == "group":
                        expanded.extend(self.expand_group(value))

        expand_entries(view.entries)

        seen: set[str] = set()

        unique: list[str] = []

        for field_name in expanded:
            if field_name in seen:
                continue

            seen.add(field_name)

            unique.append(field_name)

        return unique

    # =====================================================
    # Dashboards
    # =====================================================

    def register_dashboard(
        self,
        dashboard: DisplayDashboard,
    ):
        """
        Register DisplayDashboard.
        """

        if dashboard.name in self._dashboards:
            raise ValueError(f"Duplicate DisplayDashboard registered: {dashboard.name}")

        self._dashboards[dashboard.name] = dashboard

    def get_dashboard(
        self,
        name: str,
    ) -> DisplayDashboard:
        """
        Lookup dashboard.
        """

        try:
            return self._dashboards[name]

        except KeyError as err:
            raise KeyError(f"DisplayDashboard not found: {name}") from err

    def has_dashboard(
        self,
        name: str,
    ) -> bool:
        return name in self._dashboards

    def all_dashboards(
        self,
    ) -> list[DisplayDashboard]:
        return list(self._dashboards.values())

    def get_all_dashboards(
        self,
    ) -> list[DisplayDashboard]:
        return self.all_dashboards()

    def all_dashboard_names(
        self,
    ) -> list[str]:
        return sorted(self._dashboards.keys())

    # =====================================================
    # Diagnostics
    # =====================================================

    def summary(
        self,
    ) -> dict:
        return {
            "display_fields": len(self._display_fields),
            "groups": len(self._groups),
            "views": len(self._views),
            "dashboards": len(self._dashboards),
        }

    # =====================================================
    # Validation
    # =====================================================

    def validate(
        self,
    ):
        """
        Validate registry integrity.
        """

        # -------------------------------------------------
        # Groups
        # -------------------------------------------------

        for group in self._groups.values():
            for entry in group.entries:
                if isinstance(
                    entry,
                    str,
                ):
                    if not self.has_display_field(entry):
                        raise ValueError(
                            f"Group '{group.key}' references unknown DisplayField: {entry}"
                        )

                elif isinstance(
                    entry,
                    tuple,
                ):
                    if len(entry) != 2:
                        raise ValueError(f"Invalid group entry in '{group.key}': {entry}")

                    kind, value = entry

                    if kind == "field":
                        if not self.has_display_field(value):
                            raise ValueError(
                                f"Group '{group.key}' references unknown DisplayField: {value}"
                            )

                    elif kind == "group":
                        if not self.has_group(value):
                            raise ValueError(
                                f"Group '{group.key}' references unknown DisplayGroup: {value}"
                            )

        # -------------------------------------------------
        # Views
        # -------------------------------------------------

        for view in self._views.values():
            for entry in view.entries:
                if not isinstance(
                    entry,
                    tuple,
                ):
                    continue

                if len(entry) != 2:
                    raise ValueError(f"Invalid view entry in {view.level}/{view.name}: {entry}")

                kind, value = entry

                if kind == "group":
                    if not self.has_group(value):
                        raise ValueError(
                            f"View {view.level}/{view.name} references unknown group: {value}"
                        )

                elif kind == "field":
                    if not self.has_display_field(value):
                        raise ValueError(
                            f"View {view.level}/{view.name} references unknown field: {value}"
                        )

        # -------------------------------------------------
        # Group Cycles
        # -------------------------------------------------

        for group_name in self.all_group_names():
            self.expand_group(group_name)

    # =====================================================
    # Representation
    # =====================================================

    def __repr__(self):
        s = self.summary()

        return (
            f"DisplayRegistry("
            f"fields={s['display_fields']}, "
            f"groups={s['groups']}, "
            f"views={s['views']}, "
            f"dashboards={s['dashboards']}"
            f")"
        )

    # =====================================================
    # Convenience Aliases
    # =====================================================

    def expand_view(
        self,
        level: str,
        name: str,
    ) -> list[str]:
        """
        Convenience alias.

        Returns the fully expanded
        field list for a view.
        """

        return self.expand_view_fields(
            level,
            name,
        )
