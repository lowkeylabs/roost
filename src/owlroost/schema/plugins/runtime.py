from ..registry import FieldSpec
from ..system_models import RuntimeConfig
from ..utils import unwrap_annotation, walk_model


class RuntimePlugin:
    def register(self, registry):
        for name, field in walk_model("", RuntimeConfig):
            registry.register(
                FieldSpec(
                    name=f"runtime.{name}",
                    dtype=unwrap_annotation(field.annotation),
                    path=("runtime",) + tuple(name.split(".")),
                    source="input",
                    description=field.description or "",
                )
            )
