# src/owlroost/schema/plugins/longevity.py

from ..registry import FieldSpec


class LongevityPlugin:
    def register(self, registry):
        registry.register(
            FieldSpec(
                name="longevity.sex",
                dtype=list[str],
                path=("longevity", "sex"),
                source="input",
                description="Sex for longevity modeling",
            )
        )

        registry.register(
            FieldSpec(
                name="longevity.seed",
                dtype=int,
                path=("longevity", "seed"),
                source="input",
            )
        )
