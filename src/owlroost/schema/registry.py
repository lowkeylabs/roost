# src/owlroost/schema/registry.py

from dataclasses import dataclass, field

VALID_SOURCES = {
    "input",
    "metric",
    "derived",
    "discovered",
    "internal",
}

VALID_LEVELS = {
    "case",
    "session",
    "run",
    "trial",
}


@dataclass
class FieldSpec:
    name: str
    dtype: object

    path: tuple = field(default_factory=tuple)

    source: str = ""
    level: str = ""

    compute_fn: object | None = None
    aggregates: list = field(default_factory=list)

    # =================================================
    # Semantic metadata
    # =================================================

    description: str = ""

    variable: str = ""
    units: str | None = None
    notes: str | None = None

    doc_section: str | None = None
    doc_type: str | None = None

    default: object | None = None

    display_profiles: dict = field(default_factory=dict)

    def __post_init__(self):
        # =================================================
        # Validation
        # =================================================

        if self.source not in VALID_SOURCES:
            raise ValueError(
                f"Invalid source '{self.source}' "
                f"for field '{self.name}'. "
                f"Valid sources: "
                f"{sorted(VALID_SOURCES)}"
            )

        if self.level not in VALID_LEVELS:
            raise ValueError(
                f"Invalid level '{self.level}' "
                f"for field '{self.name}'. "
                f"Valid levels: "
                f"{sorted(VALID_LEVELS)}"
            )

        # =================================================
        # Normalize path
        # =================================================

        self.path = tuple(self.path) if self.path is not None else ()


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
