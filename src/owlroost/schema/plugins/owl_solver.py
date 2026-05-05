from owlplanner.config.ui_bridge import SOLVER_OPT_KEYS

from ..registry import FieldSpec


class OwlSolverPlugin:
    def register(self, registry):
        # -------------------------------------------------
        # Extra solver fields NOT exposed in ui_bridge
        # -------------------------------------------------
        EXTRA_SOLVER_KEYS = {
            "gap",
            "minTaxableBalance",
            "previousMAGIs",
            "timePreference",
            "withACA",
            "withDecomposition",
            "withSSAges",
        }

        # -------------------------------------------------
        # Union of all solver keys
        # -------------------------------------------------
        all_keys = set(SOLVER_OPT_KEYS) | EXTRA_SOLVER_KEYS

        # -------------------------------------------------
        # Register safely (idempotent)
        # -------------------------------------------------
        for key in all_keys:
            name = f"solver_options.{key}"

            # Skip if already registered
            if name in registry._fields:
                continue

            registry.register(
                FieldSpec(
                    name=name,
                    dtype=object,
                    path=("solver_options", key),
                    source="owl",
                    description="Derived from OWL solver configuration",
                )
            )
