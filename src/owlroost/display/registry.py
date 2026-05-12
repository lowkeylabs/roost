# src/owlroost/display/registry.py

from __future__ import annotations

from owlroost.display.specs import (
    DisplayField,
    DisplayGroup,
    ViewSpec,
)


class DisplayRegistry:
    """
    Central registry for display-layer objects.

    Owns:

    - DisplayField
    - DisplayGroup
    - ViewSpec

    This registry is intentionally separate from
    SchemaRegistry.

    SchemaRegistry owns semantic meaning.

    DisplayRegistry owns presentation semantics.
    """

    # =====================================================
    # Construction
    # =====================================================

    def __init__(self):
        self._display_fields: dict[str, DisplayField] = {}
        self._groups: dict[str, DisplayGroup] = {}
        self._views: dict[tuple[str, str], ViewSpec] = {}

    # =====================================================
    # Display Fields
    # =====================================================

    def register_display_field(
        self,
        field: DisplayField,
    ):
        """
        Register DisplayField.

        Keyed by field_name.
        """

        key = field.field_name

        #        if key in self._display_fields:
        #            raise ValueError(
        #                f"Duplicate DisplayField registered: {key}"
        #            )

        self._display_fields[key] = field

    def get_display_field(
        self,
        field_name: str,
    ) -> DisplayField:
        """
        Lookup DisplayField by field name.
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
        Return all registered display fields.
        """

        return list(self._display_fields.values())

    # =====================================================
    # Groups
    # =====================================================

    def register_group(
        self,
        group: DisplayGroup,
    ):
        """
        Register DisplayGroup.
        """

        key = group.key

        if key in self._groups:
            raise ValueError(f"Duplicate DisplayGroup registered: {key}")

        self._groups[key] = group

    def get_group(
        self,
        key: str,
    ) -> DisplayGroup:
        """
        Lookup group by key.
        """

        try:
            return self._groups[key]

        except KeyError as err:
            raise KeyError(f"DisplayGroup not found: {key}") from err

    def has_group(
        self,
        key: str,
    ) -> bool:
        """
        Return True if group exists.
        """

        return key in self._groups

    def all_groups(
        self,
    ) -> list[DisplayGroup]:
        """
        Return all groups.
        """

        return list(self._groups.values())

    # =====================================================
    # Views
    # =====================================================

    def register_view(
        self,
        view: ViewSpec,
    ):
        """
        Register ViewSpec.

        Views are uniquely identified by:

            (level, name)

        Examples:

            ("case", "basic")
            ("run", "timing")
            ("trial", "audit")
        """

        key = (view.level, view.name)

        if key in self._views:
            raise ValueError("Duplicate ViewSpec registered: " f"{view.level}/{view.name}")

        self._views[key] = view

    def get_view(
        self,
        level: str,
        name: str,
    ) -> ViewSpec:
        """
        Lookup view by (level, name).
        """

        key = (level, name)

        try:
            return self._views[key]

        except KeyError as err:
            raise KeyError(f"ViewSpec not found: {level}/{name}") from err

    def has_view(
        self,
        level: str,
        name: str,
    ) -> bool:
        """
        Return True if view exists.
        """

        return (level, name) in self._views

    def all_views(
        self,
    ) -> list[ViewSpec]:
        """
        Return all registered views.
        """

        return list(self._views.values())

    # =====================================================
    # Diagnostics
    # =====================================================

    def summary(
        self,
    ) -> dict:
        """
        Return registry summary counts.
        """

        return {
            "display_fields": len(self._display_fields),
            "groups": len(self._groups),
            "views": len(self._views),
        }

    # =====================================================
    # Validation
    # =====================================================

    def validate(self):
        """
        Validate internal references.

        Current checks:

        - groups reference valid display fields
        - views reference valid groups
        """

        # -------------------------------------------------
        # Validate groups
        # -------------------------------------------------
        for group in self._groups.values():
            for entry in group.entries:
                # -----------------------------
                # String field reference
                # -----------------------------
                if isinstance(entry, str):
                    if not self.has_display_field(entry):
                        raise ValueError(
                            "Group "
                            f"'{group.key}' "
                            "references unknown "
                            f"DisplayField: {entry}"
                        )

                # -----------------------------
                # Tuple references
                # -----------------------------
                elif isinstance(entry, tuple):
                    if len(entry) != 2:
                        raise ValueError(
                            "Invalid group tuple " f"entry in '{group.key}': " f"{entry}"
                        )

                    kind, value = entry

                    if kind == "field":
                        if not self.has_display_field(value):
                            raise ValueError(
                                "Group "
                                f"'{group.key}' "
                                "references unknown "
                                f"DisplayField: {value}"
                            )

                    elif kind == "group":
                        if not self.has_group(value):
                            raise ValueError(
                                "Group "
                                f"'{group.key}' "
                                "references unknown "
                                f"DisplayGroup: {value}"
                            )

        # -------------------------------------------------
        # Validate views
        # -------------------------------------------------
        for view in self._views.values():
            for entry in view.entries:
                # -----------------------------
                # Tuple references
                # -----------------------------
                if isinstance(entry, tuple):
                    if len(entry) != 2:
                        raise ValueError(
                            "Invalid view tuple "
                            f"entry in "
                            f"{view.level}/{view.name}: "
                            f"{entry}"
                        )

                    kind, value = entry

                    # -------------------------
                    # Group reference
                    # -------------------------
                    if kind == "group":
                        if not self.has_group(value):
                            raise ValueError(
                                "View "
                                f"{view.level}/{view.name} "
                                "references unknown "
                                f"group: {value}"
                            )

                    # -------------------------
                    # Field reference
                    # -------------------------
                    elif kind == "field":
                        if not self.has_display_field(value):
                            raise ValueError(
                                "View "
                                f"{view.level}/{view.name} "
                                "references unknown "
                                f"field: {value}"
                            )

    # =====================================================
    # Representation
    # =====================================================

    def __repr__(
        self,
    ):
        s = self.summary()

        return (
            "DisplayRegistry("
            f"fields={s['display_fields']}, "
            f"groups={s['groups']}, "
            f"views={s['views']}"
            ")"
        )
