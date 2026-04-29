# src/owlroost/schema/plugins/spending_policy.py

from ..registry import FieldSpec


class SpendingPolicyPlugin:
    def register(self, registry):
        registry.register(
            FieldSpec(
                name="spending_policy.essential",
                dtype=float,
                path=("spending_policy", "essential"),
                source="input",
            )
        )

        registry.register(
            FieldSpec(
                name="spending_policy.lifestyle",
                dtype=float,
                path=("spending_policy", "lifestyle"),
                source="input",
            )
        )
