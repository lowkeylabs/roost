from ..registry import FieldSpec
from ..system_models import RoostConfig
from ..utils import unwrap_annotation, walk_model


class RoostPlugin:
    def register(self, registry):
        for name, field in walk_model("", RoostConfig):
            registry.register(
                FieldSpec(
                    name=f"roost.{name}",
                    dtype=unwrap_annotation(field.annotation),
                    path=("roost",) + tuple(name.split(".")),
                    source="input",
                    description=field.description or "",
                )
            )
