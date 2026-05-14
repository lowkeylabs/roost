# src/owlroost/schema/plugins/owl.py

from owlplanner.config.schema import CaseConfig

from ..registry import FieldSpec
from ..utils import unwrap_annotation, walk_model


class OwlSchemaPlugin:
    def register(self, registry):
        for name, field in walk_model("", CaseConfig):
            registry.register(
                FieldSpec(
                    name=name,
                    dtype=unwrap_annotation(field.annotation),
                    path=tuple(name.split(".")),
                    source="input",
                    level="case",
                    description=field.description,
                )
            )
