# src/owlroost/schema/registry.py


VALID_SOURCES = {
    "input",
    "metric",
    "derived",
    "discovered",
    "internal",
}

VALID_LEVELS = {
    "case",
    "experiment",
    "run",
    "trial",
}


class FieldSpec:
    def __init__(
        self,
        name,
        dtype,
        *,
        path=None,
        source,
        level,
        compute_fn=None,
        aggregates=None,
        description=None,
        default=None,
        display_profiles=None,
    ):
        # =================================================
        # Validation
        # =================================================

        if source not in VALID_SOURCES:
            raise ValueError(
                f"Invalid source '{source}' "
                f"for field '{name}'. "
                f"Valid sources: "
                f"{sorted(VALID_SOURCES)}"
            )

        if level not in VALID_LEVELS:
            raise ValueError(
                f"Invalid level '{level}' "
                f"for field '{name}'. "
                f"Valid levels: "
                f"{sorted(VALID_LEVELS)}"
            )

        # =================================================
        # Core
        # =================================================

        self.name = name
        self.dtype = dtype
        self.path = tuple(path) if path is not None else ()

        # =================================================
        # Semantics
        # =================================================

        self.source = source
        self.level = level

        # =================================================
        # Behavior
        # =================================================

        self.compute_fn = compute_fn
        self.aggregates = aggregates or []

        # =================================================
        # Metadata
        # =================================================

        self.description = description or ""
        self.default = default
        self.display_profiles = display_profiles or {}


class SchemaRegistry:
    def __init__(self):
        self._fields = {}

    # =====================================================
    # Registration
    # =====================================================

    def register(
        self,
        field: FieldSpec,
    ):
        if field.name in self._fields:
            raise ValueError(f"Duplicate field registered: " f"{field.name}")

        self._fields[field.name] = field

    # =====================================================
    # Lookup
    # =====================================================

    def get(
        self,
        name,
    ):
        try:
            return self._fields[name]

        except KeyError as err:
            raise KeyError(f"Field not found: {name}") from err

    def all(self):
        return self._fields.values()

    # =====================================================
    # Discovered defaults
    # =====================================================

    def attach_discovered_defaults(
        self,
        discovered_defaults: dict,
        get_from_path,
    ):
        """
        Inject discovered defaults
        (from OWL runtime discovery)
        into FieldSpec objects.
        """

        for f in self._fields.values():
            if not f.path:
                continue

            val = get_from_path(
                discovered_defaults,
                f.path,
            )

            if val is None:
                continue

            # ---------------------------------------------
            # Only override if schema didn't already define
            # a default.
            # ---------------------------------------------

            if f.default is None:
                f.default = val

    # =====================================================
    # Discovered field registration
    # =====================================================

    def register_discovered_fields(
        self,
        discovered_defaults: dict,
    ):
        """
        Add fields that exist in discovered
        defaults but not in schema.

        Fully recursive across dicts + lists.
        """

        def walk(
            obj,
            prefix=(),
        ):
            # ---------------------------------------------
            # Dicts
            # ---------------------------------------------

            if isinstance(
                obj,
                dict,
            ):
                for k, v in obj.items():
                    path = prefix + (k,)

                    name = ".".join(path)

                    # -------------------------------------
                    # Register if missing
                    # -------------------------------------

                    if name not in self._fields:
                        self._fields[name] = FieldSpec(
                            name=name,
                            dtype=type(v),
                            path=path,
                            source="discovered",
                            level="case",
                            default=v,
                        )

                    # -------------------------------------
                    # Recurse
                    # -------------------------------------

                    walk(
                        v,
                        path,
                    )

            # ---------------------------------------------
            # Lists
            # ---------------------------------------------

            elif isinstance(
                obj,
                list,
            ):
                for item in obj:
                    walk(
                        item,
                        prefix,
                    )

            # ---------------------------------------------
            # Scalars
            # ---------------------------------------------
            else:
                pass

        walk(discovered_defaults)
