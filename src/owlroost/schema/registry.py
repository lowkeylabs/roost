# src/owlroost/schema/registry.py

# src/owlroost/schema/registry.py


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
        self.path = path
        self.source = source
        self.compute_fn = compute_fn
        self.aggregates = aggregates or []
        self.description = description


class SchemaRegistry:
    def __init__(self):
        self._fields = {}

    def register(self, field: FieldSpec):
        self._fields[field.name] = field

    def get(self, name):
        return self._fields[name]

    def all(self):
        return self._fields.values()
