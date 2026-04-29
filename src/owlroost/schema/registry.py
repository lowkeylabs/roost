# src/owlroost/schema/registry.py


class SchemaRegistry:
    def __init__(self):
        self._fields = {}

    def register(self, name, spec):
        self._fields[name] = spec

    def get(self, name):
        return self._fields[name]
