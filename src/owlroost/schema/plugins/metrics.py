from ..metrics_model import MetricsModel
from ..registry import FieldSpec
from ..utils import unwrap_annotation, walk_model


class MetricsSchemaPlugin:
    def register(self, registry):
        for name, field in walk_model("", MetricsModel):
            registry.register(
                FieldSpec(
                    name=name,
                    dtype=unwrap_annotation(field.annotation),
                    path=tuple(name.split(".")),
                    source="metric",
                    level="trial",
                    description=field.description,
                )
            )
