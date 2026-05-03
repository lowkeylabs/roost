class FieldSpec:
    def __init__(
        self,
        name,
        dtype,
        path=None,
        source="input",
        compute_fn=None,
        aggregates=None,
        description=None,
        default=None,
        default_source=None,  # ("schema" | "runtime")
    ):
        self.name = name
        self.dtype = dtype
        self.path = tuple(path) if path is not None else ()
        self.source = source
        self.compute_fn = compute_fn
        self.aggregates = aggregates or []
        self.description = description or ""

        # 👇 NEW
        self.default = default
        self.default_source = default_source


class SchemaRegistry:
    def __init__(self):
        self._fields = {}

    def register(self, field: FieldSpec):
        if field.name in self._fields:
            raise ValueError(f"Duplicate field registered: {field.name}")
        self._fields[field.name] = field

    def get(self, name):
        try:
            return self._fields[name]
        except KeyError as err:
            raise KeyError(f"Field not found: {name}") from err

    def all(self):
        return self._fields.values()

    def attach_runtime_defaults(self, runtime_defaults: dict, get_from_path):
        """
        Inject runtime defaults (from OWL) into FieldSpec objects.
        """

        for f in self._fields.values():
            if not f.path:
                continue

            val = get_from_path(runtime_defaults, f.path)

            if val is None:
                continue

            # Only override if schema didn't already define a default
            if f.default is None:
                f.default = val
                f.default_source = "runtime"

    def register_runtime_fields(self, runtime_defaults: dict):
        """
        Add fields that exist in runtime defaults but not in schema.
        Fully recursive across dicts + lists.
        """

        def walk(obj, prefix=()):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    path = prefix + (k,)
                    name = ".".join(path)

                    if name not in self._fields:
                        self._fields[name] = FieldSpec(
                            name=name,
                            dtype=type(v),
                            path=path,
                            source="runtime",
                            default=v,
                            default_source="runtime",
                        )

                    # 🔥 ALWAYS recurse
                    walk(v, path)

            elif isinstance(obj, list):
                for item in obj:
                    walk(item, prefix)

            # scalars: nothing further

        walk(runtime_defaults)
