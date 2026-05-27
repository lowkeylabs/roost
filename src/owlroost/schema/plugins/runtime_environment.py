from ..registry import FieldSpec
from ..system_models import RuntimeEnvironmentConfig
from ..utils import unwrap_annotation, walk_model


class RuntimeEnvironmentPlugin:
    root = "runtime_environment"
    model = RuntimeEnvironmentConfig

    def register(self, registry):
        for name, field in walk_model("", RuntimeEnvironmentConfig):
            full_name = f"runtime_environment.{name}"

            if full_name in registry._fields:
                continue

            registry.register(
                FieldSpec(
                    name=full_name,
                    dtype=unwrap_annotation(field.annotation),
                    path=("runtime_environment",) + tuple(name.split(".")),
                    source="input",
                    materialization_level="case",
                    description=field.description or "",
                )
            )
