# src/owlroost/schema/plugins/hydra_helpers.py

from __future__ import annotations

from ..registry import FieldSpec


class HydraHelperPlugin:
    """
    Semantic Hydra helper fields.

    These fields:

        - are sweepable
        - are NOT canonical OWL fields
        - expand into canonical fields
        - are removed after expansion
    """

    def register(
        self,
        registry,
    ):
        # =================================================
        # Historical window helper
        # =================================================

        registry.register(
            FieldSpec(
                name="rates_selection.from_to",
                dtype=str,
                path=(
                    "rates_selection",
                    "from_to",
                ),
                source="helper",
                materialization_level="run",
                description=(
                    "Historical market window "
                    "formatted as YYYY-YYYY."
                ),
            )
        )

        # =================================================
        # Named market regime
        # =================================================

        registry.register(
            FieldSpec(
                name="rates_selection.regime",
                dtype=str,
                path=(
                    "rates_selection",
                    "regime",
                ),
                source="helper",
                materialization_level="run",
                description=(
                    "Named historical "
                    "market regime."
                ),
            )
        )

        # =================================================
        # Social Security age pair
        # =================================================

        registry.register(
            FieldSpec(
                name="fixed_income.ss_age_pair",
                dtype=str,
                path=(
                    "fixed_income",
                    "ss_age_pair",
                ),
                source="helper",
                materialization_level="run",
                description=(
                    "Social Security claiming "
                    "age pair formatted as "
                    "AA.A-AA.A."
                ),
            )
        )

        # =================================================
        # Semantic optimization helper
        # =================================================

        registry.register(
            FieldSpec(
                name="roost_runtime.optimization_goal",
                dtype=str,
                path=(
                    "roost_runtime",
                    "optimization_goal",
                ),
                source="helper",
                materialization_level="run",
                description=(
                    "Semantic optimization "
                    "helper."
                ),
            )
        )
