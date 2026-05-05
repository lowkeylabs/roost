from ..registry import FieldSpec
from ..system_models import TrialConfig
from ..utils import unwrap_annotation, walk_model


class TrialPlugin:
    def register(self, registry):
        for name, field in walk_model("", TrialConfig):
            full_name = f"trial.{name}"

            if full_name in registry._fields:
                continue

            registry.register(
                FieldSpec(
                    name=f"trial.{name}",
                    dtype=unwrap_annotation(field.annotation),
                    path=("trial",) + tuple(name.split(".")),
                    source="input",
                    description=field.description or "",
                )
            )
