# src/owlroost/schema/plugins/owl.py

from owlplanner.config.schema import CaseConfig

from ..registry import FieldSpec
from ..runtime_defaults import build_runtime_defaults
from ..utils import unwrap_annotation, walk_model


class OwlSchemaPlugin:
    def register(self, registry):
        # ----------------------------------------
        # 1. Static OWL schema (Pydantic)
        # ----------------------------------------
        for name, field in walk_model("", CaseConfig):
            registry.register(
                FieldSpec(
                    name=name,
                    dtype=unwrap_annotation(field.annotation),
                    path=tuple(name.split(".")),
                    source="input",
                    description=field.description,
                )
            )

        # ----------------------------------------
        # 2. Runtime-expanded OWL fields
        # ----------------------------------------
        runtime_defaults = build_runtime_defaults()

        def walk(d, prefix=()):
            for k, v in d.items():
                path = prefix + (k,)
                name = ".".join(path)

                if name not in registry._fields:
                    registry._fields[name] = FieldSpec(
                        name=name,
                        dtype=type(v),
                        path=path,
                        source="runtime",
                        default=v,
                        default_source="runtime",
                    )

                if isinstance(v, dict):
                    walk(v, path)

        walk(runtime_defaults)
