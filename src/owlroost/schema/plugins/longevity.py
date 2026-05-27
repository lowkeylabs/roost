# src/owlroost/schema/plugins/longevity.py

from ..registry import FieldSpec
from ..system_models import LongevityConfig
from ..utils import unwrap_annotation, walk_model


class LongevityPlugin:
    root = "longevity"
    model = LongevityConfig

    def register(self, registry):
        for name, field in walk_model("", LongevityConfig):
            full_name = f"longevity.{name}"

            # -------------------------------------------------
            # Skip duplicates (important for merged schema)
            # -------------------------------------------------
            if full_name in registry._fields:
                continue

            registry.register(
                FieldSpec(
                    name=full_name,
                    dtype=unwrap_annotation(field.annotation),
                    path=("longevity",) + tuple(name.split(".")),
                    source="input",
                    materialization_level="case",
                    description=field.description or "",
                )
            )
