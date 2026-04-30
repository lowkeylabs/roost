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
    ):
        self.name = name
        self.dtype = dtype
        self.path = tuple(path) if path is not None else ()
        self.source = source
        self.compute_fn = compute_fn
        self.aggregates = aggregates or []
        self.description = description or ""


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
