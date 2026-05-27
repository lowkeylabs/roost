# src/owlroost/schema/plugins/roost_runtime.py

from ..registry import FieldSpec
from ..system_models import RoostRuntimeConfig
from ..utils import (
    resolve_field_default,
    unwrap_annotation,
    walk_model,
)


class RoostRuntimePlugin:
    root = "roost_runtime"
    model = RoostRuntimeConfig

    def register(self, registry):
        for name, field in walk_model("", RoostRuntimeConfig):
            full_name = f"roost_runtime.{name}"

            # -------------------------------------------------
            # Skip duplicates (important for merged schema)
            # -------------------------------------------------

            if full_name in registry._fields:
                continue

            registry.register(
                FieldSpec(
                    name=full_name,
                    dtype=unwrap_annotation(field.annotation),
                    path=("roost_runtime",) + tuple(name.split(".")),
                    source="input",
                    materialization_level="case",
                    description=field.description or "",
                    default=resolve_field_default(field),
                )
            )
