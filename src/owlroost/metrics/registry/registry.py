class MetricsRegistry:
    def __init__(self):
        self._fields = {}

    def register(
        self,
        field,
    ):
        if field.name in self._fields:
            return

        self._fields[field.name] = field

    def get(
        self,
        name,
    ):
        return self._fields[name]

    def all(self):
        return list(self._fields.values())
