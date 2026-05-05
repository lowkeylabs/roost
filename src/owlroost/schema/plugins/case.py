from ..registry import FieldSpec
from ..system_models import CaseConfig
from ..utils import unwrap_annotation, walk_model


class CasePlugin:
    def register(self, registry):
        for name, field in walk_model("", CaseConfig):
            registry.register(
                FieldSpec(
                    name=f"case.{name}",
                    dtype=unwrap_annotation(field.annotation),
                    path=("case",) + tuple(name.split(".")),
                    source="input",
                    description=field.description or "",
                )
            )
