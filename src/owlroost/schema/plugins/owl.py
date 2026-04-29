# src/owlroost/schema/plugins/owl.py

from owlplanner.config.schema import CaseConfig

from owlroost.schema.registry import FieldSpec


def walk_model(prefix, model):
    for name, field in model.model_fields.items():
        full_name = f"{prefix}.{name}" if prefix else name

        yield full_name, field

        if hasattr(field.annotation, "model_fields"):
            yield from walk_model(full_name, field.annotation)


class OwlSchemaPlugin:
    def register(self, registry):
        for name, field in walk_model("", CaseConfig):
            registry.register(
                FieldSpec(
                    name=name,
                    dtype=field.annotation,
                    path=tuple(name.split(".")),
                    source="input",
                    description=field.description,
                )
            )
