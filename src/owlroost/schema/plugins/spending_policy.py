# src/owlroost/schema/plugins/spending_policy.py

from ..registry import FieldSpec
from ..system_models import SpendingPolicyConfig
from ..utils import unwrap_annotation, walk_model


class SpendingPolicyPlugin:
    root = "spending_policy"
    model = SpendingPolicyConfig

    def register(self, registry):
        for name, field in walk_model("", SpendingPolicyConfig):
            full_name = f"spending_policy.{name}"

            # -------------------------------------------------
            # Skip duplicates (important for merged schema)
            # -------------------------------------------------
            if full_name in registry._fields:
                continue

            registry.register(
                FieldSpec(
                    name=full_name,
                    dtype=unwrap_annotation(field.annotation),
                    path=("spending_policy",) + tuple(name.split(".")),
                    source="input",
                    level="case",
                    description=field.description or "",
                )
            )
